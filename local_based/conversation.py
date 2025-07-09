from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict
from roles import Role

@dataclass
class Conversation:
    """Holds chat history + current user query."""

    user_query: str
    history: List[Dict[str, str]] = field(default_factory=list)

    def append_message(self, role: Role, content: str) -> None:
        self.history.append({"role": role, "content": content})

    def get_conversation(self, *, n_last_messages: int = -1) -> List[Dict[str, str]]:
        if n_last_messages == -1:
            return self.history + [{"role": Role.USER, "content": self.user_query}]
        return self.history[-n_last_messages:] + [{"role": Role.USER, "content": self.user_query}]

    def clear(self) -> None:
        self.history.clear()