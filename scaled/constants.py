"""Project‑wide literal constants."""
SYSTEM_PROMPT = (
    "You are an agent designed to interact with an SQL database representing an IFC model of a building.\n"
    "Given an input question, create a syntactically correct SQLite query, execute via tools, and answer.\n"
    "Never perform DML. When comparing strings use LIKE and lower().\n"
    "Always double‑check queries, consider previous context, and prefix final answer with ‘CONFIRMED’."
)

DEFAULT_GEN_KWARGS = {
    "max_new_tokens": 2048,
    "temperature": 0.6,
    "top_p": 0.9,
    "do_sample": True,
    "return_full_text": False,
}

TOOL_CALL_RE = r"<tool_call>(.*?)</tool_call>"

SUGGEST_K = 5