# """Build / load cached descriptions of DB schema + helper for table suggestions."""
# from __future__ import annotations
# import json, os
# from functools import lru_cache
# from typing import Dict, List
# from langchain_community.utilities.sql_database import SQLDatabase
# from sklearn.feature_extraction.text import TfidfVectorizer
# from sklearn.metrics.pairwise import cosine_similarity

# CACHE_PATH = ".schema_cache.json"

# # ───────────────────────────── summary build ─────────────────────────────

# def build_schema_summary(db: SQLDatabase) -> Dict[str, str]:
#     summary: Dict[str, str] = {}
#     for tbl in db.get_usable_table_names():
#         cols = db.run(f"PRAGMA table_info({tbl});")
#         col_names = [c[1] for c in eval(cols)]  # PRAGMA returns SQL‑string repr
#         summary[tbl] = f"{tbl}({', '.join(col_names)})"
#     return summary

# # ───────────────────────────── cache API ─────────────────────────────────

# def load_schema_cache(db: SQLDatabase, path: str = CACHE_PATH) -> Dict[str, str]:
#     if os.path.exists(path):
#         with open(path, "r", encoding="utf‑8") as fh:
#             return json.load(fh)
#     summary = build_schema_summary(db)
#     with open(path, "w", encoding="utf‑8") as fh:
#         json.dump(summary, fh, indent=2)
#     return summary

# # ─────────────────────────── table suggestion ────────────────────────────
# _Vectorizer: TfidfVectorizer | None = None
# _DocMatrix = None
# _Tables: List[str] = []

# @lru_cache(maxsize=1)
# def _ensure_vectorizer(summary: Dict[str, str]):
#     global _Vectorizer, _DocMatrix, _Tables  # noqa: PLW0603
#     if _Vectorizer is None:
#         docs = list(summary.values())
#         _Tables = list(summary.keys())
#         _Vectorizer = TfidfVectorizer().fit(docs)
#         _DocMatrix = _Vectorizer.transform(docs)


# def suggest_tables(query: str, summary: Dict[str, str], k: int = 5) -> List[str]:
#     _ensure_vectorizer(summary)
#     q_vec = _Vectorizer.transform([query])
#     sims  = cosine_similarity(q_vec, _DocMatrix).ravel()
#     return [_Tables[i] for i in sims.argsort()[::-1][:k]]