from __future__ import annotations

import json
from collections.abc import Callable

import pytest

from examples.research._runner import WORKFLOWS_DIR, execute
from examples.research.run_python import RESEARCH_REPORT
from src.dagbuilder import build_dag, execution_order
from src.registry import Context, StepRegistry, WorkflowSpec

EXPECTED_ORDER = [
    "load_research_brief",
    "draft_research_report",
    "format_research_report",
    "render_research_pdf",
]
MOCK_CTX = Context(data={"mock_bedrock": True})


@pytest.fixture
def research_example_tasks():
    import importlib
    import sys

    module_name = "examples.research.tasks"
    if module_name not in sys.modules:
        import examples.research.tasks  # noqa: F401

    from src.registerfuncs import REGISTRY

    REGISTRY.clear()
    importlib.reload(sys.modules[module_name])
    yield sys.modules[module_name]


def _load_yaml_spec() -> WorkflowSpec:
    return WorkflowSpec.load(WORKFLOWS_DIR / "research_report.yaml")


def _load_json_spec() -> WorkflowSpec:
    payload = json.loads((WORKFLOWS_DIR / "research_report.json").read_text())
    return WorkflowSpec.model_validate(payload)


def assert_happy_path(ctx: Context) -> None:
    assert "load_research_brief" in ctx.data
    assert "draft_research_report" in ctx.data
    draft = ctx.data["draft_research_report"]
    assert isinstance(draft, dict)
    assert draft.get("turn", 1) >= 2
    assert "2025" in str(draft.get("text", ""))
    report = ctx.data["format_research_report"]
    assert report.startswith("# Research Report:")
    assert "## References" in report or "References" in report
    pdf = ctx.data.get("render_research_pdf")
    assert isinstance(pdf, dict)
    assert pdf.get("path")
    assert str(pdf["path"]).endswith(".pdf")
    assert pdf.get("download_url", "").endswith(".pdf")
    from pathlib import Path

    assert Path(pdf["path"]).stat().st_size > 5000


@pytest.mark.parametrize(
    ("name", "load_spec"),
    [
        ("python", lambda: RESEARCH_REPORT),
        ("yaml", _load_yaml_spec),
        ("json", _load_json_spec),
    ],
)
def test_research_report_mock_happy_path(
    research_example_tasks, name: str, load_spec: Callable[[], WorkflowSpec]
):
    spec = load_spec()
    assert spec.name == "research_report"

    registry = StepRegistry()
    registry.load_workflow(spec)
    graph = build_dag(registry.all())
    assert execution_order(graph) == EXPECTED_ORDER
    assert spec.steps[1].max_model_turns == 4
    assert len(spec.steps[1].resolved_evals()) == 4

    ctx = execute(spec, MOCK_CTX)
    assert_happy_path(ctx)


def test_yaml_and_json_match_python_spec(research_example_tasks):
    yaml_spec = _load_yaml_spec()
    json_spec = _load_json_spec()
    assert yaml_spec.model_dump() == json_spec.model_dump()
    assert yaml_spec.model_dump() == RESEARCH_REPORT.model_dump()


def test_research_eval_exhaustion_skips_downstream(research_example_tasks):
    ctx = execute(
        RESEARCH_REPORT,
        Context(
            data={
                "mock_bedrock": True,
                "mock_response_text": "Too thin.",
                "min_report_words": 500,
            }
        ),
    )
    assert "draft_research_report" in ctx.data
    assert "format_research_report" not in ctx.data
    assert "render_research_pdf" not in ctx.data
    assert "draft_research_report__eval_failure_reason" in ctx.data
