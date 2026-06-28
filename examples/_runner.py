from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.dagbuilder import build_dag, execution_order
from src.executor import run_workflow
from src.registry import Context, StepRegistry, WorkflowSpec

WORKFLOWS_DIR = Path(__file__).resolve().parent / "workflows"


def execute(
    spec: WorkflowSpec,
    ctx: Context | None = None,
    *,
    max_workers: int | None = None,
    task_module: str = "examples.tasks",
) -> Context:
    import importlib

    importlib.import_module(task_module)

    registry = StepRegistry()
    registry.load_workflow(spec)
    graph = build_dag(registry.all())
    result = run_workflow(graph, ctx or Context(), max_workers=max_workers)
    print(f"workflow={spec.name!r} order={execution_order(graph)}")
    if spec.name == "parallel_portfolio":
        print(f"report={result.data.get('format_portfolio_report')!r}")
        print(f"shared_quotes={result.data.get('quotes')!r}")
    else:
        print(f"report={result.data.get('format_report')!r}")
    return result
