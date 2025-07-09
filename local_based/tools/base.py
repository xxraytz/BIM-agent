from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Callable, List

@dataclass
class ToolExecutionResult:
    success: bool
    result: str
    tool_name: str


class ToolManager:
    """Registry + dispatch for callable tools."""

    def __init__(self) -> None:
        self._tools: List[dict] = []
        self._funcs: dict[str, Callable] = {}

    @property
    def tools(self) -> List[dict]:
        return self._tools

    # ───────────────────────────── API ─────────────────────────────
    def register_tool(self, tool_def: dict, func: Callable) -> None:
        self._tools.append(tool_def)
        self._funcs[tool_def["name"]] = func

    def execute_tool(self, tool_name: str, arguments: dict) -> ToolExecutionResult:
        func = self._funcs.get(tool_name)
        if not func:
            return ToolExecutionResult(False, f"Tool '{tool_name}' not found", tool_name)
        try:
            res = func(**arguments)
            return ToolExecutionResult(True, res, tool_name)
        except Exception as exc:  # noqa: BLE001
            return ToolExecutionResult(False, str(exc), tool_name)