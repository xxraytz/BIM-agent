from __future__ import annotations
import json
from typing import List
from conversation import Conversation
from roles import Role
from agent.qwen_sql import QwenSQLPrimaryAgent
from tools.sql import SQLToolManager
from models.qwen_pipeline import load_qwen_pipeline
from langchain_community.utilities.sql_database import SQLDatabase
from loguru import logger


def run(query: str, db_uri: str = "sqlite:///database.sqlite", *, max_iter: int = 10) -> None:
    db = SQLDatabase.from_uri(db_uri)
    tools = SQLToolManager(db)
    agent = QwenSQLPrimaryAgent("qwen", load_qwen_pipeline(), tool_manager=tools)

    convo = Conversation(query)
    for _ in range(max_iter):
        raw, calls = agent.respond(convo)
        print(f"Raw response: {raw}")
        convo.append_message(Role.ASSISTANT, raw)
        for call in calls:
            res = tools.execute_tool(call["name"], call.get("arguments", {}))
            print(f"Tool result: {res}")
            convo.append_message(Role.TOOL, json.dumps(res.__dict__))
        if "CONFIRMED" in raw:
            print(raw)
            return