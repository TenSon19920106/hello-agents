"""固定 PBC 载荷结构说明与轻量校验（无第三方 JSON Schema 依赖）。

本项目的「最终 JSON 契约」以本文件为准：
- SCHEMA_DOC：给 LLM / 人类看的结构说明
- validate_pbc_payload：给程序用的强约束校验（含枚举、权重合计等）
"""

from __future__ import annotations

import re
from typing import Any

# 与 README、LLM 提示词保持一致的字段约定
SCHEMA_DOC = """
顶层必须为 JSON 对象，且包含以下键（不可改名、不可缺省）：

- gh: string，工号（必填）
- khnf: integer，考核年份编码（以系统为准；本项目默认基准为 2022：2022->0,2023->1,2024->2,2025->3...）
- khjd: integer，考核季度（0:第一季度,1:第二季度,2:第三季度,3:第四季度,4:年度）
- dllzb: array，定量类指标（可为空数组）
  - khmd: string，考核目的
  - wd: integer，维度（0:财务,1:客户,2:管理及运营,3:长期成长）
  - KPI: string（注意字段名必须为大写 KPI）
  - mb: string，目标
  - ly: integer，来源（0:公司战略规划及年度目标,1:上级/内外部客户,2:部门职能及组织绩效目标,3:岗位职责,4:部门阶段性或临时性重点工作,5:其它）
  - qz: number，权重（两位小数）。dllzb 与 dxlzb 的 qz 合计必须等于 100
  - jffs: string，计分方式
- dxlzb: array，定性类指标（可为空数组）
  - khmd: string，考核目的
  - zdgz: string，重点工作/项目/人物
  - ly: integer，来源（同上）
  - qz: number，权重（两位小数），与 dllzb 合计=100
  - jffs: string，计分方式
- grcz: array，个人成长（不计入权重合计，可为空数组）
  - dtgnl: string，待提高/待发展的能力或经验
  - jhtscs: string，计划提升措施
  - sxzy: string，所需资源
  - jhwcsj: string，计划完成时间（YYYY-MM-DD）
"""

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _as_float(x: Any) -> float | None:
    if isinstance(x, (int, float)):
        return float(x)
    if isinstance(x, str):
        s = x.strip().replace("%", "")
        if not s:
            return None
        try:
            return float(s)
        except ValueError:
            return None
    return None


def validate_pbc_payload(data: Any) -> tuple[bool, list[str]]:
    """返回 (是否通过, 错误信息列表)。"""
    errors: list[str] = []
    if not isinstance(data, dict):
        return False, ["根节点必须是 JSON 对象"]

    required_roots = ("gh", "khnf", "khjd", "dllzb", "dxlzb", "grcz")
    for key in required_roots:
        if key not in data:
            errors.append(f"缺少顶层键: {key}")

    gh = data.get("gh")
    if "gh" in data and (not isinstance(gh, str) or not gh.strip()):
        errors.append("gh 必须为非空字符串（工号）")

    khnf = data.get("khnf")
    if "khnf" in data and not isinstance(khnf, int):
        errors.append("khnf 必须为整数（0:2023,1:2024...）")
    elif isinstance(khnf, int) and khnf < 0:
        errors.append("khnf 不能为负数")

    khjd = data.get("khjd")
    if "khjd" in data and not isinstance(khjd, int):
        errors.append("khjd 必须为整数（0-4）")
    elif isinstance(khjd, int) and khjd not in (0, 1, 2, 3, 4):
        errors.append("khjd 取值仅允许 0,1,2,3,4")

    wds = {0, 1, 2, 3}
    lys = {0, 1, 2, 3, 4, 5}

    total_weight = 0.0

    dllzb = data.get("dllzb")
    if "dllzb" in data:
        if not isinstance(dllzb, list):
            errors.append("dllzb 必须为数组")
        else:
            for i, item in enumerate(dllzb):
                if not isinstance(item, dict):
                    errors.append(f"dllzb[{i}] 必须为对象")
                    continue
                for k in ("khmd", "wd", "KPI", "mb", "ly", "qz", "jffs"):
                    if k not in item:
                        errors.append(f"dllzb[{i}] 缺少字段: {k}")
                if "khmd" in item:
                    v = item.get("khmd")
                    if not isinstance(v, str):
                        errors.append(f"dllzb[{i}].khmd 必须为字符串")
                    elif not v.strip():
                        errors.append(f"dllzb[{i}].khmd 不能为空")
                if "KPI" in item:
                    v = item.get("KPI")
                    if not isinstance(v, str):
                        errors.append(f"dllzb[{i}].KPI 必须为字符串")
                    elif not v.strip():
                        errors.append(f"dllzb[{i}].KPI 不能为空")
                if "mb" in item:
                    v = item.get("mb")
                    if not isinstance(v, str):
                        errors.append(f"dllzb[{i}].mb 必须为字符串")
                    elif not v.strip():
                        errors.append(f"dllzb[{i}].mb 不能为空")
                if "jffs" in item:
                    v = item.get("jffs")
                    if not isinstance(v, str):
                        errors.append(f"dllzb[{i}].jffs 必须为字符串")
                    elif not v.strip():
                        errors.append(f"dllzb[{i}].jffs 不能为空")
                if "wd" in item and (not isinstance(item.get("wd"), int) or item["wd"] not in wds):
                    errors.append(f"dllzb[{i}].wd 取值仅允许 0-3")
                if "ly" in item and (not isinstance(item.get("ly"), int) or item["ly"] not in lys):
                    errors.append(f"dllzb[{i}].ly 取值仅允许 0-5")
                if "qz" in item:
                    q = _as_float(item.get("qz"))
                    if q is None:
                        errors.append(f"dllzb[{i}].qz 必须为数字")
                    else:
                        if q < 0:
                            errors.append(f"dllzb[{i}].qz 不能为负数")
                        total_weight += q

    dxlzb = data.get("dxlzb")
    if "dxlzb" in data:
        if not isinstance(dxlzb, list):
            errors.append("dxlzb 必须为数组")
        else:
            for i, item in enumerate(dxlzb):
                if not isinstance(item, dict):
                    errors.append(f"dxlzb[{i}] 必须为对象")
                    continue
                for k in ("khmd", "zdgz", "ly", "qz", "jffs"):
                    if k not in item:
                        errors.append(f"dxlzb[{i}] 缺少字段: {k}")
                if "khmd" in item:
                    v = item.get("khmd")
                    if not isinstance(v, str):
                        errors.append(f"dxlzb[{i}].khmd 必须为字符串")
                    elif not v.strip():
                        errors.append(f"dxlzb[{i}].khmd 不能为空")
                if "zdgz" in item:
                    v = item.get("zdgz")
                    if not isinstance(v, str):
                        errors.append(f"dxlzb[{i}].zdgz 必须为字符串")
                    elif not v.strip():
                        errors.append(f"dxlzb[{i}].zdgz 不能为空")
                if "jffs" in item:
                    v = item.get("jffs")
                    if not isinstance(v, str):
                        errors.append(f"dxlzb[{i}].jffs 必须为字符串")
                    elif not v.strip():
                        errors.append(f"dxlzb[{i}].jffs 不能为空")
                if "ly" in item and (not isinstance(item.get("ly"), int) or item["ly"] not in lys):
                    errors.append(f"dxlzb[{i}].ly 取值仅允许 0-5")
                if "qz" in item:
                    q = _as_float(item.get("qz"))
                    if q is None:
                        errors.append(f"dxlzb[{i}].qz 必须为数字")
                    else:
                        if q < 0:
                            errors.append(f"dxlzb[{i}].qz 不能为负数")
                        total_weight += q

    # 权重校验：dllzb+dxlzb 的 qz 合计必须等于 100（允许 0.01 误差）
    if isinstance(dllzb, list) and isinstance(dxlzb, list):
        if len(dllzb) + len(dxlzb) > 0:
            if abs(total_weight - 100.0) > 0.01:
                errors.append(f"dllzb+dxlzb 权重合计必须为 100（当前 {total_weight:.2f}）")

    grcz = data.get("grcz")
    if "grcz" in data:
        if not isinstance(grcz, list):
            errors.append("grcz 必须为数组")
        else:
            for i, item in enumerate(grcz):
                if not isinstance(item, dict):
                    errors.append(f"grcz[{i}] 必须为对象")
                    continue
                for k in ("dtgnl", "jhtscs", "sxzy", "jhwcsj"):
                    if k not in item:
                        errors.append(f"grcz[{i}] 缺少字段: {k}")
                for k in ("dtgnl", "jhtscs", "sxzy"):
                    if k in item and not isinstance(item.get(k), str):
                        errors.append(f"grcz[{i}].{k} 必须为字符串")
                if "jhwcsj" in item:
                    v = item.get("jhwcsj")
                    if not isinstance(v, str) or not _DATE_RE.match(v.strip()):
                        errors.append(f"grcz[{i}].jhwcsj 必须为 YYYY-MM-DD 格式字符串")

    return len(errors) == 0, errors
