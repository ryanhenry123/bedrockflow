"""Load and run research_report from JSON."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from examples.research._runner import WORKFLOWS_DIR, execute
from src.registry import Context, WorkflowSpec


def main() -> None:
    spec = WorkflowSpec.load(WORKFLOWS_DIR / "research_report.json")
    execute(spec, Context(data={}))


if __name__ == "__main__":
    main()
