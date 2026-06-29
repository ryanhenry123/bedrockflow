"""Demonstrate eval failure: model returns, validator rejects, downstream skipped."""

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
                "thesis": "Eval fail demo",
                "mock_bedrock": True,
                "mock_response_text": "Too short.",
                "min_response_chars": 500,
            }
        ),
    )


if __name__ == "__main__":
    main()
