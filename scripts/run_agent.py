"""CLI wrapper that injects ./src into sys.path automatically."""
from __future__ import annotations
import os, sys, argparse, pathlib

# ── add ./src to import path ───────────────────────────────────────────
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC_PATH  = REPO_ROOT / "local_based"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from runner import run  # now import works

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("query", help="User question")
    parser.add_argument("--db", default="sqlite:///database.sqlite")
    parser.add_argument("--max-iter", type=int, default=10)
    args = parser.parse_args()

    run(args.query, db_uri=args.db, max_iter=args.max_iter)