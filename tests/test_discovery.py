from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ui.discovery import discover_workflows, get_workflow, reload_workflow_catalog


@pytest.fixture(autouse=True)
def fresh_catalog():
    reload_workflow_catalog()
    yield
    reload_workflow_catalog()


def test_discovers_all_example_workflows():
    names = sorted(discover_workflows())
    assert names == ["aws_risk_summary", "daily_report", "parallel_portfolio"]


def test_resolves_task_modules():
    assert get_workflow("daily_report").task_module == "examples.tasks"
    assert get_workflow("parallel_portfolio").task_module == "examples.parallel_tasks"
    assert get_workflow("aws_risk_summary").task_module == "examples.aws.tasks"


def test_infers_report_keys():
    assert get_workflow("daily_report").report_key == "format_report"
    assert get_workflow("parallel_portfolio").report_key == "format_portfolio_report"
    assert get_workflow("aws_risk_summary").report_key == "format_memo"


def test_parallel_portfolio_infers_max_workers():
    assert get_workflow("parallel_portfolio").max_workers == 2


def test_aws_default_context_uses_live_bedrock_model():
    ctx = get_workflow("aws_risk_summary").default_context
    assert ctx.get("model_id") == "amazon.nova-lite-v1:0"
    assert "mock_bedrock" not in ctx
    assert ctx.get("symbol") == "AAPL"


def test_duplicate_workflow_name_raises(tmp_path: Path):
    workflows = tmp_path / "workflows"
    workflows.mkdir()
    (workflows / "one.yaml").write_text(
        "name: dup\ntask_module: examples.tasks\nsteps:\n"
        "  - step_name: load_symbol\n    caller: load_symbol\n    depends_on: []\n"
    )
    nested = tmp_path / "nested" / "workflows"
    nested.mkdir(parents=True)
    (nested / "two.yaml").write_text(
        "name: dup\ntask_module: examples.tasks\nsteps:\n"
        "  - step_name: load_symbol\n    caller: load_symbol\n    depends_on: []\n"
    )

    with pytest.raises(ValueError, match="Duplicate workflow name"):
        discover_workflows(tmp_path)
