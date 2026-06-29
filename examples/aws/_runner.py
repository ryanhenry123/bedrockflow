from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from examples._runner import execute as _execute
from src.registry import Context, WorkflowSpec

WORKFLOWS_DIR = Path(__file__).resolve().parent / "workflows"
TASK_MODULE = "examples.aws.tasks"


def execute(
    spec: WorkflowSpec,
    ctx: Context | None = None,
    *,
    max_workers: int | None = None,
) -> Context:
    result = _execute(
        spec,
        ctx,
        max_workers=max_workers,
        task_module=TASK_MODULE,
        report_key=None,
    )
    _print_outcome(result)
    return result


def _print_outcome(ctx: Context) -> None:
    if memo := ctx.data.get("format_memo"):
        print(f"memo={memo!r}")
        return
    if reason := ctx.data.get("eval_failure_reason"):
        print(f"eval_failed reason={reason!r}")
        return
    if error := ctx.data.get("bedrock_error"):
        print(f"bedrock_error={error!r} type={ctx.data.get('bedrock_error_type')!r}")
        return
    print(f"context_keys={sorted(ctx.data.keys())!r}")
