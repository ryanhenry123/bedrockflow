"""Demonstrate failure handler: caller raises, on_failure runs, downstream skipped."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from examples.aws._runner import execute
from examples.aws.run_python import AWS_RISK_SUMMARY
from src.registry import Context


def main() -> None:
    execute(
        AWS_RISK_SUMMARY,
        Context(
            data={
                "symbol": "AAPL",
                "thesis": "Failure handler demo",
                "mock_bedrock": True,
                "force_bedrock_error": True,
            }
        ),
    )


if __name__ == "__main__":
    main()
