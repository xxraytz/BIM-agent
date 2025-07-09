from __future__ import annotations
import abc, re, json
from typing import List, Tuple
from conversation import Conversation
from roles import Role
from tools.base import ToolManager
from constants import DEFAULT_GEN_KWARGS, TOOL_CALL_RE

class Agent(abc.ABC):
    """Abstract agent template."""

    def __init__(self, name: str, model_pipeline, *, tool_manager: ToolManager | None = None):
        self.name = name
        self.pipeline = model_pipeline
        self.tool_manager = tool_manager

    # ─────────────────────────────────────────────────────────────────────
    def respond(self, convo: Conversation, **gen_kwargs) -> Tuple[str, List[dict]]:
        prompt = self._construct_prompt(convo)
        gen = {**DEFAULT_GEN_KWARGS, **gen_kwargs}
        resp = self.pipeline(prompt, **gen)[0]["generated_text"]
        tool_calls = self._extract_tool_calls(resp) if self.tool_manager else []
        return resp, tool_calls

    # ───────────────────────── abstract hooks ────────────────────────────
    @abc.abstractmethod
    def _construct_prompt(self, convo: Conversation) -> str: ...

    # ───────────────────────────── helpers ───────────────────────────────
    def _extract_tool_calls(self, text: str) -> List[dict]:
        calls: List[dict] = []
        for part in re.findall(TOOL_CALL_RE, text, re.S):
            try:
                calls.append(json.loads(part))
            except json.JSONDecodeError:  # ignore silently
                continue
        return calls