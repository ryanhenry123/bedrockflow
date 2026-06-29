"""Mock-mode research report runner for CI and offline use."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from examples.research._runner import execute
from examples.research.run_python import RESEARCH_REPORT
from src.registry import Context


def main() -> None:
    execute(
        RESEARCH_REPORT,
        Context(data={"mock_bedrock": True}),
    )


if __name__ == "__main__":
    main()
