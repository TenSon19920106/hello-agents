"""信息完整性检查：发现缺口后，用固定话术或 LLM 生成追问，便于用户二次补充。

注意：本项目 JSON 结构以 `schema.py` 为准；本模块只做「业务可读」层面的缺口提示。
"""

from __future__ import annotations

from typing import Any

from hello_agents import HelloAgentsLLM, SimpleAgent


def list_information_gaps(
    payload: dict[str, Any],
    *,
    min_khmd_chars: int = 8,
) -> list[str]:
    """基于规则的缺口列表（与 validate_pbc_payload 是否通过无关）。"""
    gaps: list[str] = []

    if not str(payload.get("gh") or "").strip():
        gaps.append("工号 gh 为空，请补充。")

    dllzb = payload.get("dllzb") or []
    dxlzb = payload.get("dxlzb") or []
    if not isinstance(dllzb, list):
        dllzb = []
    if not isinstance(dxlzb, list):
        dxlzb = []

    if len(dllzb) == 0 and len(dxlzb) == 0:
        gaps.append("定量/定性指标均为空：请至少补充一类指标条目。")

    for i, it in enumerate(dllzb):
        if not isinstance(it, dict):
            continue
        khmd = str(it.get("khmd") or "").strip()
        if len(khmd) < min_khmd_chars or "原文未提及" in khmd:
            gaps.append(f"定量指标 dllzb[{i}] 的考核目的(khmd)过短或缺少依据，请补充。")

    for i, it in enumerate(dxlzb):
        if not isinstance(it, dict):
            continue
        zdgz = str(it.get("zdgz") or "").strip()
        if len(zdgz) < min_khmd_chars or "原文未提及" in zdgz:
            gaps.append(f"定性指标 dxlzb[{i}] 的重点工作(zdgz)过短或缺少依据，请补充。")

    grcz = payload.get("grcz") or []
    if isinstance(grcz, list) and len(grcz) == 0:
        gaps.append("个人成长 grcz 为空：如本季度无成长计划，可写一条占位说明。")

    return gaps


def format_gaps_for_user(gaps: list[str]) -> str:
    return "\n".join(f"{i + 1}. {g}" for i, g in enumerate(gaps))


def merge_raw_with_supplement(raw: str, supplement: str) -> str:
    """把用户第二次输入拼到原文后，再送给结构化 Agent。"""
    return raw.strip() + "\n\n【用户补充说明】\n" + supplement.strip()


def suggest_follow_up_questions(
    llm: HelloAgentsLLM,
    *,
    raw_text: str,
    gaps: list[str],
) -> str:
    """用 LLM 把缺口转写为给业务用户看的简短追问（可选）。"""
    if not gaps:
        return ""
    agent = SimpleAgent(
        name="追问生成",
        llm=llm,
        system_prompt="你是绩效助手。根据缺口列表生成给员工的补充提问，语气正式简短。只输出编号列表，不要 JSON。",
    )
    prompt = (
        "员工已提交的工作叙述如下：\n---\n"
        f"{raw_text[:6000]}\n---\n"
        "系统发现以下缺口：\n"
        f"{format_gaps_for_user(gaps)}\n"
        "请输出 3～8 条追问，帮助员工一次性补全信息。"
    )
    return agent.run(prompt).strip()
