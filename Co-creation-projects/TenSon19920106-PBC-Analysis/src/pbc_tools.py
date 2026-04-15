"""供 SimpleAgent 调用的工具：读文件、提交绩效制订/反馈接口。"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

from hello_agents.tools import Tool, ToolParameter, ToolResponse
from hello_agents.tools.errors import ToolErrorCode

from . import api_client
from . import io_utils


class ReadWorkSummaryTool(Tool):
    """仅允许读取项目 data/ 目录下的文本，避免任意路径读取。"""

    def __init__(self, data_root: str | Path | None = None):
        super().__init__(
            name="read_work_summary_file",
            description="读取 data/ 目录下的工作总结文本文件（utf-8），返回文件内容字符串",
        )
        self._data_root = Path(data_root) if data_root else Path(__file__).resolve().parent.parent / "data"

    def run(self, parameters: Dict[str, Any]) -> ToolResponse:
        name = (parameters.get("filename") or "").strip()
        if not name or ".." in name or "/" in name or "\\" in name:
            return ToolResponse.error(
                code=ToolErrorCode.INVALID_PARAM,
                message="filename 只能为 data/ 下的文件名，不含路径分隔符",
            )
        path = (self._data_root / name).resolve()
        try:
            path.relative_to(self._data_root.resolve())
        except ValueError:
            return ToolResponse.error(code=ToolErrorCode.ACCESS_DENIED, message="路径越界")
        if not path.is_file():
            return ToolResponse.error(
                code=ToolErrorCode.NOT_FOUND,
                message=f"文件不存在: {path.name}",
            )
        try:
            content = io_utils.load_text_file(path)
            return ToolResponse.success(text=content, data={"filename": name})
        except Exception as e:
            return ToolResponse.error(
                code=ToolErrorCode.EXECUTION_ERROR,
                message=str(e),
            )

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="filename",
                type="string",
                description="相对于 data/ 的文件名，例如 sample_quarterly_work.txt",
                required=True,
            )
        ]


class SubmitPbcPlanningTool(Tool):
    def __init__(self):
        super().__init__(
            name="submit_pbc_planning",
            description="将完整 PBC JSON 以 POST 方式提交到绩效制订接口（环境变量 PBC_PLANNING_URL）",
        )

    def run(self, parameters: Dict[str, Any]) -> ToolResponse:
        raw = parameters.get("payload_json", "")
        if not raw:
            return ToolResponse.error(
                code=ToolErrorCode.INVALID_PARAM,
                message="需要 payload_json（字符串形式的 JSON）",
            )
        try:
            payload = json.loads(raw) if isinstance(raw, str) else raw
        except json.JSONDecodeError as e:
            return ToolResponse.error(
                code=ToolErrorCode.INVALID_FORMAT,
                message=f"JSON 解析失败: {e}",
            )
        if not isinstance(payload, dict):
            return ToolResponse.error(
                code=ToolErrorCode.INVALID_FORMAT,
                message="payload 必须是 JSON 对象",
            )
        url = os.getenv("PBC_PLANNING_URL", "").strip()
        if not url:
            msg = "干跑：未配置 PBC_PLANNING_URL，未发起请求。载荷顶层键: " + ",".join(payload.keys())
            return ToolResponse.success(
                text=msg,
                data={"dry_run": True, "keys": list(payload.keys())},
            )
        try:
            code, body = api_client.post_json(url, payload, token=os.getenv("PBC_API_TOKEN") or None)
            return ToolResponse.success(
                text=f"HTTP {code}\n{body[:4000]}",
                data={"http_status": code},
            )
        except Exception as e:
            return ToolResponse.error(
                code=ToolErrorCode.NETWORK_ERROR,
                message=f"请求失败: {e}",
            )

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="payload_json",
                type="string",
                description="完整 PBC 对象的 JSON 字符串",
                required=True,
            )
        ]


class SubmitPbcFeedbackTool(Tool):
    def __init__(self):
        super().__init__(
            name="submit_pbc_feedback",
            description="将完整 PBC JSON 以 POST 方式提交到绩效反馈接口（环境变量 PBC_FEEDBACK_URL）",
        )

    def run(self, parameters: Dict[str, Any]) -> ToolResponse:
        raw = parameters.get("payload_json", "")
        if not raw:
            return ToolResponse.error(
                code=ToolErrorCode.INVALID_PARAM,
                message="需要 payload_json",
            )
        try:
            payload = json.loads(raw) if isinstance(raw, str) else raw
        except json.JSONDecodeError as e:
            return ToolResponse.error(
                code=ToolErrorCode.INVALID_FORMAT,
                message=f"JSON 解析失败: {e}",
            )
        if not isinstance(payload, dict):
            return ToolResponse.error(
                code=ToolErrorCode.INVALID_FORMAT,
                message="payload 必须是 JSON 对象",
            )
        url = os.getenv("PBC_FEEDBACK_URL", "").strip()
        if not url:
            return ToolResponse.success(
                text="干跑：未配置 PBC_FEEDBACK_URL，未发起请求。",
                data={"dry_run": True},
            )
        try:
            code, body = api_client.post_json(url, payload, token=os.getenv("PBC_API_TOKEN") or None)
            return ToolResponse.success(
                text=f"HTTP {code}\n{body[:4000]}",
                data={"http_status": code},
            )
        except Exception as e:
            return ToolResponse.error(
                code=ToolErrorCode.NETWORK_ERROR,
                message=f"请求失败: {e}",
            )

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="payload_json",
                type="string",
                description="完整 PBC 对象的 JSON 字符串",
                required=True,
            )
        ]
