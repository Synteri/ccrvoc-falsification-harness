from __future__ import annotations

import argparse

from ccrvoc.config import load_config
from ccrvoc.diagnostic import run_diagnostic
from ccrvoc.experiment import finalize_existing, run_experiment


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("--config", required=True)
    run.add_argument("--output", default="artifacts")
    diagnostic = sub.add_parser("diagnostic")
    diagnostic.add_argument("--config", required=True)
    diagnostic.add_argument("--output", default="artifacts/repair_diagnostic")
    finalize = sub.add_parser("finalize")
    finalize.add_argument("--config", required=True)
    finalize.add_argument("--output", default="artifacts")
    finalize.add_argument("--executed-commit", required=True)
    args = parser.parse_args()
    if args.command == "run":
        status = run_experiment(load_config(args.config), args.output)
        print(status)
    elif args.command == "diagnostic":
        status = run_diagnostic(load_config(args.config), args.output)
        print(status)
    elif args.command == "finalize":
        status = finalize_existing(load_config(args.config), args.output, args.executed_commit)
        print(status)


if __name__ == "__main__":
    main()
