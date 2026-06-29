"""Build and run the parallel_portfolio workflow entirely in Python."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from examples._runner import execute
from src.registry import Context, StepSpec, WorkflowSpec

PARALLEL_PORTFOLIO = WorkflowSpec(
    name="parallel_portfolio",
    max_workers=2,
    default_context={"symbols": ["AAPL", "MSFT"]},
    steps=[
        StepSpec(step_name="load_watchlist", caller="load_watchlist"),
        StepSpec(
            step_name="fetch_aapl",
            caller="fetch_aapl",
            depends_on=["load_watchlist"],
        ),
        StepSpec(
            step_name="fetch_msft",
            caller="fetch_msft",
            depends_on=["load_watchlist"],
        ),
        StepSpec(
            step_name="aggregate_portfolio",
            caller="aggregate_portfolio",
            depends_on=["fetch_aapl", "fetch_msft"],
        ),
        StepSpec(
            step_name="format_portfolio_report",
            caller="format_portfolio_report",
            depends_on=["aggregate_portfolio"],
        ),
    ],
)


def main() -> None:
    execute(
        PARALLEL_PORTFOLIO,
        Context(data={"symbols": ["AAPL", "MSFT"]}),
        max_workers=2,
        task_module="examples.parallel_tasks",
    )


if __name__ == "__main__":
    main()
