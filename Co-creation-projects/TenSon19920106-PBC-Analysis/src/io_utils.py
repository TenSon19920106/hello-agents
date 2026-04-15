from __future__ import annotations

from pathlib import Path


def load_text_file(path: str | Path, *, max_chars: int = 120_000) -> str:
    """读取 UTF-8 文本；用于 .txt / .md 等工作总结文件。"""
    p = Path(path).expanduser().resolve()
    if not p.is_file():
        raise FileNotFoundError(str(p))
    text = p.read_text(encoding="utf-8", errors="replace")
    if len(text) > max_chars:
        raise ValueError(f"文件过长（>{max_chars} 字符），请拆分或提高上限")
    return text.strip()
