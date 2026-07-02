from __future__ import annotations

import argparse
import sys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="orchflow",
        description="Bedrock eval loops and offline eval panels.",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("run", help="Run the trade memo Bedrock example")

    eval_p = sub.add_parser(
        "eval",
        help="Run an eval panel on fixture file(s) or directories (*.md, *.txt)",
    )
    eval_p.add_argument(
        "paths",
        nargs="+",
        help="Fixture files or directories",
    )
    eval_p.add_argument(
        "--panel",
        default="orchflow.examples.evals:DRAFT_EVALS",
        help="Eval panel as module.path:ATTRIBUTE (default: trade memo panel)",
    )
    eval_p.add_argument(
        "--ctx",
        default=None,
        help="JSON context passed to evals, e.g. '{\"max_words\":600}'",
    )
    eval_p.add_argument(
        "--stop-reason",
        default="end_turn",
        help="Simulated stop reason (default: end_turn)",
    )

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "eval":
        from orchflow.evals.offline import parse_ctx_json, run_eval_cli

        ctx = parse_ctx_json(args.ctx)
        code = run_eval_cli(
            args.paths,
            panel=args.panel,
            ctx=ctx,
            stop_reason=args.stop_reason,
        )
        raise SystemExit(code)

    from orchflow.examples.trade_memo import main as run_example

    run_example()


if __name__ == "__main__":
    main()
