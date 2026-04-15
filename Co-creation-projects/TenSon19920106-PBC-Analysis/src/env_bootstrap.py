"""解决 Jupyter 工作目录不一致、以及系统环境变量残留导致的 LLM 配置不生效问题。"""

from __future__ import annotations

import os
from pathlib import Path


def find_project_root(start: Path | None = None) -> Path:
    """
    优先定位到包含 main.ipynb 的本项目目录（不依赖「从哪启动 jupyter」）。
    """
    cwd = Path.cwd().resolve() if start is None else Path(start).resolve()
    if (cwd / "main.ipynb").is_file() and (cwd / "src" / "extract.py").is_file():
        return cwd
    alt = cwd / "Co-creation-projects" / "TenSon19920106-PBC-Analysis"
    if (alt / "main.ipynb").is_file():
        return alt
    for p in cwd.parents:
        hit = p / "Co-creation-projects" / "TenSon19920106-PBC-Analysis" / "main.ipynb"
        if hit.is_file():
            return hit.parent
    return cwd


def apply_env_file(env_path: Path) -> bool:
    """
    直接从磁盘 .env 写入 os.environ（覆盖同名变量），避免：
    - load_dotenv(override=False) 时系统里旧的 LLM_MODEL_ID 优先生效
    - 工作目录错误导致读到别的 .env
    """
    try:
        from dotenv import dotenv_values
    except ImportError:
        return False
    if not env_path.is_file():
        return False
    for k, v in dotenv_values(env_path).items():
        if v is None:
            continue
        s = str(v).strip()
        if s == "":
            continue
        os.environ[k] = s
    return True


def bootstrap(start: Path | None = None) -> Path:
    root = find_project_root(start)
    apply_env_file(root / ".env")
    return root
