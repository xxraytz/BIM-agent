from __future__ import annotations
import argparse

from scaled.runner import run as run_scaled

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", help="User question")
    parser.add_argument("--db", default="sqlite:///database.sqlite")
    parser.add_argument("--max-iter", type=int, default=10)
    parser.add_argument("--method", type=str, default="scaled")
    args = parser.parse_args()
    if args.method == "scaled":
        run_scaled(args.query, db_uri=args.db, max_iter=args.max_iter)
    else:
        from full_context_based.core import main as run_buildin_context

        assert run_buildin_context is not None
        run_buildin_context(args.query)
