from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

from hello_agents import HelloAgentsLLM, SimpleAgent

from .schema import SCHEMA_DOC, validate_pbc_payload


def _fill_defaults(data: dict[str, Any]) -> dict[str, Any]:
    """
    业务兜底：部分字段即使原文未提及，也给一个可接受的默认值，
    避免出现“原文未提及/请补充”影响提交与展示。

    注意：gh/khnf/khjd 仍然必须由用户输入（不在这里兜底）。
    """
    # 定量/定性：若缺 jffs 或为空/占位，则补默认计分方式
    def _need_fill(v: Any) -> bool:
        if not isinstance(v, str):
            return True
        s = v.strip()
        if not s:
            return True
        return "原文未提及" in s or "请补充" in s

    dllzb = data.get("dllzb")
    if isinstance(dllzb, list):
        for it in dllzb:
            # 兼容旧字段名：kpi -> KPI（流程表单要求大写 KPI）
            if isinstance(it, dict) and "KPI" not in it and "kpi" in it:
                it["KPI"] = it.pop("kpi")
            if isinstance(it, dict) and _need_fill(it.get("jffs")):
                it["jffs"] = "按目标达成度计分（可按完成率/是否达标/超额完成分档）"

    dxlzb = data.get("dxlzb")
    if isinstance(dxlzb, list):
        for it in dxlzb:
            if isinstance(it, dict) and _need_fill(it.get("jffs")):
                it["jffs"] = "按交付质量与影响力计分（可按完成情况+评语综合）"

    return data


def _strip_code_fence(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = re.sub(r"^```(?:json)?\s*", "", t, flags=re.IGNORECASE)
        t = re.sub(r"\s*```$", "", t)
    return t.strip()


def parse_llm_json(text: str) -> dict[str, Any]:
    raw = _strip_code_fence(text)
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("模型输出中未找到 JSON 对象")
    return json.loads(raw[start : end + 1])


def build_structuring_prompt(*, gh: str, khnf: int, khjd: int) -> str:
    return f"""你是企业绩效系统中「PBC/指标」结构化专员。
用户会粘贴一段本季度/年度工作情况（口语化段落或条目）。

你的任务：只输出 **一个** JSON 对象，不要任何解释、不要 Markdown、不要注释。
JSON 必须严格满足下列结构（键名与层级不可更改）：

{SCHEMA_DOC}

补充规则（务必遵守）：
- 输出必须是标准 JSON：使用英文双引号 \\" \\"，不要使用中文引号
- gh/khnf/khjd **不得推断、不得给默认值**：必须使用我在下方提供的「用户输入值」
- 你必须将 gh 设置为：\"{gh}\"
- 你必须将 khnf 设置为：{khnf}
- 你必须将 khjd 设置为：{khjd}
- qz 必须为数字（两位小数优先），且 dllzb 与 dxlzb 的 qz 合计必须等于 100
- 不要编造不存在的数据；信息不足时允许写“原文未提及/请补充”，但字段必须齐全

用户原文如下：
"""


def build_validator_prompt() -> str:
    return f"""你是 JSON 校验与修复助手。你会收到一段文本，其中应包含一个 PBC 业务 JSON。
若已是合法 JSON 且满足结构：{SCHEMA_DOC}

请只输出修复后的 **一个** JSON 对象，不要其它文字。
修复重点：
- 引号必须为英文双引号
- 字段必须齐全，类型正确（khnf/khjd/wd/ly 为整数，qz 为数字，grcz.jhwcsj 为 YYYY-MM-DD）
- dllzb+dxlzb 的 qz 合计必须为 100（允许 0.01 误差）

若无法修复，输出 {{"error":"原因简述"}}"""


def extract_pbc_payload(
    llm: HelloAgentsLLM,
    raw_text: str,
    *,
    gh: str,
    khnf: int,
    khjd: int,
) -> dict[str, Any]:
    if not isinstance(gh, str) or not gh.strip():
        raise ValueError("gh（工号）必须由用户输入，且不能为空")
    if not isinstance(khnf, int):
        raise ValueError("khnf（考核年份）必须由用户输入，且必须为整数")
    if not isinstance(khjd, int):
        raise ValueError("khjd（考核季度）必须由用户输入，且必须为整数")
    agent = SimpleAgent(
        name="PBC结构化助手",
        llm=llm,
        system_prompt="你只输出合法 JSON 对象；字段名与类型必须满足提示中的 SCHEMA。",
    )
    prompt = build_structuring_prompt(gh=gh.strip(), khnf=khnf, khjd=khjd) + "\n---\n" + raw_text.strip()
    out = agent.run(prompt)
    data = parse_llm_json(out)
    data = _fill_defaults(data)
    ok, errs = validate_pbc_payload(data)
    if ok:
        return data
    repair = SimpleAgent(
        name="PBC校验修复助手",
        llm=llm,
        system_prompt="你只输出 JSON。",
    )
    fix_prompt = build_validator_prompt() + "\n---\n当前输出如下，请修复：\n" + json.dumps(
        data, ensure_ascii=False, indent=2
    ) + "\n---\n校验错误：\n" + "\n".join(errs)
    fixed_text = repair.run(fix_prompt)
    fixed = parse_llm_json(fixed_text)
    fixed = _fill_defaults(fixed)
    if "error" in fixed and len(fixed) == 1:
        raise ValueError(f"无法生成合法 PBC JSON: {fixed['error']}")
    ok2, errs2 = validate_pbc_payload(fixed)
    if not ok2:
        raise ValueError("二次修复仍失败: " + "; ".join(errs2))
    return fixed


def fill_submitted_at_if_missing(payload: dict[str, Any]) -> dict[str, Any]:
    """若 LLM 未填 submitted_at，补 UTC 时间。"""
    meta = payload.get("meta")
    if not isinstance(meta, dict):
        return payload
    if not meta.get("submitted_at"):
        meta = {**meta, "submitted_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
        return {**payload, "meta": meta}
    return payload
