"""Build and run the aws_risk_summary workflow in Python (live Bedrock)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from examples.aws._runner import execute
from examples.aws.tasks import DEFAULT_MODEL_ID
from src.registry import Context, StepSpec, WorkflowSpec

AWS_RISK_SUMMARY = WorkflowSpec(
    name="aws_risk_summary",
    default_context={
        "symbol": "AAPL",
        "thesis": "Long gamma into earnings",
        "model_id": "amazon.nova-lite-v1:0",
    },
    steps=[
        StepSpec(step_name="load_thesis", caller="load_thesis"),
        StepSpec(
            step_name="summarize_risk",
            caller="summarize_risk",
            eval="validate_summary",
            on_failure="handle_bedrock_failure",
            depends_on=["load_thesis"],
        ),
        StepSpec(
            step_name="format_memo",
            caller="format_memo",
            depends_on=["summarize_risk"],
        ),
    ],
)


def main() -> None:
    execute(
        AWS_RISK_SUMMARY,
        Context(
            data={
                "symbol": "AAPL",
                "thesis": "Long gamma into earnings",
                "model_id": DEFAULT_MODEL_ID,
            }
        ),
    )


if __name__ == "__main__":
    main()
