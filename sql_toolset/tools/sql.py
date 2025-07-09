from __future__ import annotations
import ast, json
from typing import List
from langchain_community.utilities.sql_database import SQLDatabase
from ..tools.base import ToolManager

class SQLToolManager(ToolManager):
    """Provides list‑tables / schema / query / query‑checker over SQLDatabase."""

    def __init__(self, db: SQLDatabase):
        super().__init__()
        self.db = db
        # self.schema_summary = metadata.load_schema_cache(db)
        self._init_tools()

    # ───────────────────────── internal helpers ─────────────────────────
    def _init_tools(self) -> None:
        self.register_tool(
            {
                "name": "sql_db_list_tables",
                "description": "Return comma‑separated list of tables (optionally skip empty)",
                "parameters": {
                    "type": "object",
                    "properties": {"list_empty_tables": {"type": "boolean", "default": False}},
                },
            },
            self.sql_db_list_tables,
        )

        self.register_tool(
            {
                "name": "sql_db_schema",
                "description": "Get schema & sample rows for tables",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "tables": {"type": "string"},
                        "n_samples": {"type": "integer", "default": 3},
                    },
                    "required": ["tables"],
                },
            },
            self.sql_db_schema,
        )

        self.register_tool(
            {
                "name": "sql_db_query_checker",
                "description": "Validate SQL query before execution",
                "parameters": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                },
            },
            self.sql_db_query_checker,
        )

        self.register_tool(
            {
                "name": "sql_db_query",
                "description": "Execute SQL query (after validation)",
                "parameters": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                },
            },
            self.sql_db_query,
        )

    # ───────────────────────── tool impls ─────────────────────────
    def sql_db_list_tables(self, list_empty_tables: bool = False) -> str:
        tables = self.db.get_usable_table_names()
        if not list_empty_tables:
            tables = [t for t in tables if self._table_has_rows(t)]
        return ", ".join(tables)

    def _table_has_rows(self, table: str) -> bool:
        res = self.db.run(f"SELECT COUNT(*) FROM {table};")
        return ast.literal_eval(res)[0][0] > 0

    def sql_db_schema(self, tables: str, n_samples: int = 3) -> str:
        out: List[str] = []
        for tbl in [t.strip() for t in tables.split(",") if t.strip()]:
            schema = self.db.get_table_info([tbl])
            sample = self.db.run(f"SELECT * FROM {tbl} LIMIT {n_samples};")
            out.append(f"Table {tbl}\n{schema}\nSample rows: {sample}")
        return "\n\n".join(out)

    def sql_db_query_checker(self, query: str) -> str:
        try:
            self.db.run_no_throw(query)
            res = self.db.run(query)
            if not res or ast.literal_eval(res)[0][0] == 0:
                return "Query valid but returns no rows"
            return "Query valid and returns rows"
        except Exception as exc:
            return f"Query error: {exc}"

    def sql_db_query(self, query: str) -> str:
        try:
            res = self.db.run(query)
            return json.dumps(res)
        except Exception as exc:
            return f"Execution error: {exc}"