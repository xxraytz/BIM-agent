from __future__ import annotations
from typing import List
from .sql_primary import SQLPrimaryAgent
from ..constants import SYSTEM_PROMPT, DEFAULT_GEN_KWARGS
import json

class QwenSQLPrimaryAgent(SQLPrimaryAgent):
    """Specialisation for Qwen – only tweaks generation defaults if needed."""

    def __init__(self, name, pipeline, *, tool_manager=None, n_history=10):
        super().__init__(name, pipeline, tool_manager=tool_manager, n_history=n_history)
        self.n_history = n_history
        self.stop_tokens = ["<|im_end|>"] 

    def _generate_response(self, prompt: str, **kwargs) -> str:
        # breakpoint()
        gen = {**DEFAULT_GEN_KWARGS, "stop": self.stop_tokens, **kwargs}
        return self.pipeline(prompt, **gen)[0]["generated_text"]