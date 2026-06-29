"""Build and run research_report entirely in Python."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from examples.research._runner import execute
from src.registry import Context, StepSpec, WorkflowSpec

RESEARCH_REPORT = WorkflowSpec(
    name="research_report",
    default_context={
        "topic": "Systematic volatility selling crowding and tail risk (2024-2026)",
        "model_id": "amazon.nova-lite-v1:0",
    },
    steps=[
        StepSpec(step_name="load_research_brief", caller="load_research_brief"),
        StepSpec(
            step_name="draft_research_report",
            caller="draft_research_report",
            evals=[
                "eval_report_structure",
                "eval_report_recency",
                "eval_report_references",
                "eval_report_depth",
            ],
            max_model_turns=4,
            on_failure="handle_research_failure",
            depends_on=["load_research_brief"],
        ),
        StepSpec(
            step_name="format_research_report",
            caller="format_research_report",
            depends_on=["draft_research_report"],
        ),
        StepSpec(
            step_name="render_research_pdf",
            caller="render_research_pdf",
            depends_on=["format_research_report"],
        ),
    ],
)


def main() -> None:
    execute(RESEARCH_REPORT, Context(data={}))


if __name__ == "__main__":
    main()
