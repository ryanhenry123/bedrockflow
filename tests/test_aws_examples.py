from __future__ import annotations

import json
from collections.abc import Callable

import pytest

from examples.aws._runner import WORKFLOWS_DIR, execute
from examples.aws.run_python import AWS_RISK_SUMMARY
from src.dagbuilder import build_dag, execution_order
from src.registry import Context, StepRegistry, WorkflowSpec

EXPECTED_ORDER = ["load_thesis", "summarize_risk", "format_memo"]
MOCK_CTX = Context(
    data={
        "symbol": "AAPL",
        "thesis": "Long gamma",
        "mock_bedrock": True,
    }
)


@pytest.fixture
def aws_example_tasks():
    import importlib
    import sys

    module_name = "examples.aws.tasks"
    if module_name not in sys.modules:
        import examples.aws.tasks  # noqa: F401

    from src.registerfuncs import REGISTRY

    REGISTRY.clear()
    importlib.reload(sys.modules[module_name])
    yield sys.modules[module_name]


def _load_yaml_spec() -> WorkflowSpec:
    return WorkflowSpec.load(WORKFLOWS_DIR / "risk_summary.yaml")


def _load_json_spec() -> WorkflowSpec:
    payload = json.loads((WORKFLOWS_DIR / "risk_summary.json").read_text())
    return WorkflowSpec.model_validate(payload)


def assert_happy_path(ctx: Context) -> None:
    assert ctx.data["load_thesis"]["symbol"] == "AAPL"
    assert "summarize_risk" in ctx.data
    assert "text" in ctx.data["summarize_risk"]
    assert ctx.data["summarize_risk"].get("turn", 1) >= 1
    assert "format_memo" in ctx.data
    assert "AAPL RISK MEMO" in ctx.data["format_memo"]
    assert "bedrock_error" not in ctx.data


@pytest.mark.parametrize(
    ("name", "load_spec"),
    [
        ("python", lambda: AWS_RISK_SUMMARY),
        ("yaml", _load_yaml_spec),
        ("json", _load_json_spec),
    ],
)
def test_aws_risk_summary_mock_happy_path(
    aws_example_tasks, name: str, load_spec: Callable[[], WorkflowSpec]
):
    spec = load_spec()
    assert spec.name == "aws_risk_summary"

    registry = StepRegistry()
    registry.load_workflow(spec)
    graph = build_dag(registry.all())
    assert execution_order(graph) == EXPECTED_ORDER

    ctx = execute(spec, MOCK_CTX)
    assert_happy_path(ctx)


def test_yaml_and_json_match_python_spec(aws_example_tasks):
    yaml_spec = _load_yaml_spec()
    json_spec = _load_json_spec()
    assert yaml_spec.model_dump() == json_spec.model_dump()
    assert yaml_spec.model_dump() == AWS_RISK_SUMMARY.model_dump()


def test_eval_fail_skips_downstream(aws_example_tasks):
    ctx = execute(
        AWS_RISK_SUMMARY,
        Context(
            data={
                "symbol": "AAPL",
                "mock_bedrock": True,
                "mock_response_text": "Risk exists.",
                "min_response_chars": 500,
            }
        ),
    )
    assert "summarize_risk" in ctx.data
    assert "format_memo" not in ctx.data
    assert "summarize_risk__eval_failure_reason" in ctx.data
    assert "bedrock_error" not in ctx.data


def test_failure_handler_skips_downstream(aws_example_tasks):
    ctx = execute(
        AWS_RISK_SUMMARY,
        Context(
            data={
                "symbol": "AAPL",
                "mock_bedrock": True,
                "force_bedrock_error": True,
            }
        ),
    )
    assert "summarize_risk" not in ctx.data
    assert "format_memo" not in ctx.data
    assert ctx.data["bedrock_error_type"] == "RuntimeError"
    assert "forced bedrock failure" in ctx.data["bedrock_error"]


def test_run_mock_main(aws_example_tasks, capsys):
    from examples.aws.run_mock import main

    main()
    captured = capsys.readouterr().out
    assert "workflow='aws_risk_summary'" in captured
    assert "AAPL RISK MEMO" in captured
