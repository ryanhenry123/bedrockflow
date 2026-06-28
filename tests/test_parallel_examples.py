from __future__ import annotations

import json
from collections.abc import Callable

import pytest

from examples._runner import WORKFLOWS_DIR, execute
from examples.run_parallel_python import PARALLEL_PORTFOLIO
from src.dagbuilder import build_dag, execution_order
from src.registry import Context, StepRegistry, WorkflowSpec

PARALLEL_CTX = Context(data={"symbols": ["AAPL", "MSFT"]})
EXPECTED_REPORT = "portfolio[AAPL,MSFT]: avg=280.81 over 8 ticks"
EXPECTED_QUOTES = {
    "AAPL": {"count": 4, "avg": 150.75},
    "MSFT": {"count": 4, "avg": 410.875},
}


def _load_yaml_spec() -> WorkflowSpec:
    return WorkflowSpec.load(WORKFLOWS_DIR / "parallel_portfolio.yaml")


def _load_json_spec() -> WorkflowSpec:
    payload = json.loads((WORKFLOWS_DIR / "parallel_portfolio.json").read_text())
    return WorkflowSpec.model_validate(payload)


def assert_parallel_portfolio_result(ctx: Context) -> None:
    assert ctx.data["load_watchlist"] == ["AAPL", "MSFT"]
    assert ctx.data["quotes"] == EXPECTED_QUOTES
    assert ctx.data["aggregate_portfolio"] == {
        "symbols": 2,
        "avg": 280.8125,
        "total_ticks": 8,
    }
    assert ctx.data["format_portfolio_report"] == EXPECTED_REPORT


@pytest.mark.parametrize(
    ("name", "load_spec"),
    [
        ("python", lambda: PARALLEL_PORTFOLIO),
        ("yaml", _load_yaml_spec),
        ("json", _load_json_spec),
    ],
)
def test_parallel_portfolio_executes(
    parallel_example_tasks,
    name: str,
    load_spec: Callable[[], WorkflowSpec],
):
    spec = load_spec()
    assert spec.name == "parallel_portfolio"

    registry = StepRegistry()
    registry.load_workflow(spec)
    graph = build_dag(registry.all())
    assert set(execution_order(graph)[:3]) == {
        "load_watchlist",
        "fetch_aapl",
        "fetch_msft",
    }

    ctx = execute(
        spec,
        PARALLEL_CTX,
        max_workers=2,
        task_module="examples.parallel_tasks",
    )
    assert_parallel_portfolio_result(ctx)


def test_parallel_specs_match_python(parallel_example_tasks):
    yaml_spec = _load_yaml_spec()
    json_spec = _load_json_spec()
    assert yaml_spec.model_dump() == json_spec.model_dump()
    assert yaml_spec.model_dump() == PARALLEL_PORTFOLIO.model_dump()


def test_run_parallel_python_main(parallel_example_tasks, capsys):
    from examples.run_parallel_python import main

    main()
    captured = capsys.readouterr().out
    assert "workflow='parallel_portfolio'" in captured
    assert f"report={EXPECTED_REPORT!r}" in captured
    assert "shared_quotes=" in captured
