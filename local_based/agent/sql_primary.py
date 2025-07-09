from __future__ import annotations
from typing import List
from agent.base import Agent
from constants import SYSTEM_PROMPT
from roles import Role
import json


class SQLPrimaryAgent(Agent):
    """LLM that reasons + issues SQL tools."""

    def __init__(self, name, model_pipeline, *, tool_manager=None, n_history=10):
        super().__init__(name, model_pipeline, tool_manager=tool_manager)
        if self.tool_manager.tools:
            self.tool_section = [
                "# Tools\nYou may call one or more functions to assist with the user query.\nYou are provided with function signatures within <tools></tools> XML tags:\n<tools>",
                "<tools>",
                *[json.dumps(tool, indent=2) for tool in self.tool_manager.tools],
                "</tools>",
                "\nFor function calls use:",
                "<tool_call>",
                "{\"name\": \"function\", \"arguments\": {\"arg\": \"value\"}}",
                "</tool_call>"
            ]

    def _construct_prompt(self, convo):
        schema_text = ""
        if self.tool_manager and hasattr(self.tool_manager, "schema_summary"):
            schema_lines = [
                f"{tbl}: {cols}"
                for tbl, cols in self.tool_manager.schema_summary.items()
            ]
            # schema_text = "# Schema Summary\n" + "\n".join(schema_lines) + "\n"

        tools_section = "\n".join(self.tool_section) if hasattr(self, "tool_section") else ""

        parts: List[str] = [
            f"<|im_start|>system\n"
            f"{SYSTEM_PROMPT}\n"
            f"{schema_text}"
            f"{tools_section}"
            f"<|im_end|>"
        ]

        for msg in convo.get_conversation(n_last_messages=self.n_history):
            parts.append(f"<|im_start|>{msg['role']}\n{msg['content']}<|im_end|>")

        parts.append("<|im_start|>assistant\n")
        return "\n".join(parts)
