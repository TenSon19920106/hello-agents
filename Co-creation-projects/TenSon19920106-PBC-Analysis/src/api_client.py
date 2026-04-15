from __future__ import annotations

import json
import os
from typing import Any

import requests


def _headers(token: str | None) -> dict[str, str]:
    h = {"Content-Type": "application/json; charset=utf-8"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _env_flag(name: str, default: bool) -> bool:
    v = str(os.getenv(name, "")).strip().lower()
    if v in ("1", "true", "yes", "y", "on"):
        return True
    if v in ("0", "false", "no", "n", "off"):
        return False
    return default


def post_json(
    url: str,
    payload: dict[str, Any],
    *,
    token: str | None = None,
    timeout: int = 60,
    verify_ssl: bool = True,
) -> tuple[int, str]:
    """POST JSON，返回 (HTTP 状态码, 响应正文文本)。"""
    resp = requests.post(
        url,
        headers=_headers(token),
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        timeout=timeout,
        verify=verify_ssl,
    )
    return resp.status_code, resp.text[:8000]


def submit_planning(payload: dict[str, Any]) -> tuple[int, str] | None:
    url = os.getenv("PBC_PLANNING_URL", "").strip()
    if not url:
        return None
    timeout = int(os.getenv("PBC_API_TIMEOUT", "60"))
    verify_ssl = _env_flag("PBC_VERIFY_SSL", True)
    return post_json(url, payload, token=os.getenv("PBC_API_TOKEN") or None, timeout=timeout, verify_ssl=verify_ssl)


def submit_feedback(payload: dict[str, Any]) -> tuple[int, str] | None:
    url = os.getenv("PBC_FEEDBACK_URL", "").strip()
    if not url:
        return None
    timeout = int(os.getenv("PBC_API_TIMEOUT", "60"))
    verify_ssl = _env_flag("PBC_VERIFY_SSL", True)
    return post_json(url, payload, token=os.getenv("PBC_API_TOKEN") or None, timeout=timeout, verify_ssl=verify_ssl)
