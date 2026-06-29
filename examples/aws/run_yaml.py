"""Load and run aws_risk_summary from YAML (live Bedrock)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from examples.aws._runner import WORKFLOWS_DIR, execute
from examples.aws.tasks import DEFAULT_MODEL_ID
from src.registry import Context, WorkflowSpec


def main() -> None:
    spec = WorkflowSpec.load(WORKFLOWS_DIR / "risk_summary.yaml")
    execute(
        spec,
        Context(
            data={
                "symbol": "MSFT",
                "thesis": "Short vol on post-guidance drift",
                "model_id": DEFAULT_MODEL_ID,
            }
        ),
    )


if __name__ == "__main__":
    main()
