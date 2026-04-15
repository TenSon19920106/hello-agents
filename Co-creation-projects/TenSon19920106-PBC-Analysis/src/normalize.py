from __future__ import annotations

import os
from typing import Any


def _base_year() -> int:
    """
    khnf 编码基准年份。
    默认 2022（这样 2025 -> 3），可通过环境变量 KHNF_BASE_YEAR 覆盖。
    """
    v = str(os.getenv("KHNF_BASE_YEAR", "2022")).strip()
    try:
        return int(v)
    except ValueError:
        return 2022


def normalize_khnf(value: Any) -> int:
    """
    khnf 规范化：
    - 若输入为年份（如 2026），转换为编码（base->0, base+1->1...）
    - 若输入为编码（如 3），保持不变
    """
    if value is None:
        raise ValueError("KHNF 不能为空")

    # bool 是 int 的子类，提前拦一下
    if isinstance(value, bool):
        raise ValueError("KHNF 必须为整数编码或年份，不允许布尔值")

    if isinstance(value, int):
        base = _base_year()
        # 年份（经验规则：>=base 视为年份）
        if value >= base:
            return value - base
        return value

    if isinstance(value, str):
        s = value.strip()
        if not s:
            raise ValueError("KHNF 不能为空字符串")
        if s.isdigit():
            return normalize_khnf(int(s))
        raise ValueError(f"无法解析 KHNF: {value!r}，请填 2026 或 3 这类数字")

    raise ValueError(f"无法解析 KHNF: {value!r}")


_KHJD_MAP = {
    "第一季度": 0,
    "第二季度": 1,
    "第三季度": 2,
    "第四季度": 3,
    "年度": 4,
    "年": 4,
    "q1": 0,
    "q2": 1,
    "q3": 2,
    "q4": 3,
}


def normalize_khjd(value: Any) -> int:
    """khjd 规范化：支持 0~4、'第一季度'、'Q1'、'年度' 等。"""
    if value is None:
        raise ValueError("KHJD 不能为空")

    if isinstance(value, bool):
        raise ValueError("KHJD 必须为整数或季度文本，不允许布尔值")

    if isinstance(value, int):
        if value not in (0, 1, 2, 3, 4):
            raise ValueError("KHJD 取值仅允许 0,1,2,3,4")
        return value

    if isinstance(value, str):
        s = value.strip()
        if not s:
            raise ValueError("KHJD 不能为空字符串")
        s2 = s.lower().replace("季度", "季度").replace(" ", "")
        if s2.isdigit():
            return normalize_khjd(int(s2))
        if s2 in _KHJD_MAP:
            return _KHJD_MAP[s2]
        # 兼容 “第一/第二...” 但省略“季度”
        if s2 in ("第一", "一"):
            return 0
        if s2 in ("第二", "二"):
            return 1
        if s2 in ("第三", "三"):
            return 2
        if s2 in ("第四", "四"):
            return 3
        raise ValueError(f"无法解析 KHJD: {value!r}，请填 0~4 或 第一季度/Q1/年度")

    raise ValueError(f"无法解析 KHJD: {value!r}")

