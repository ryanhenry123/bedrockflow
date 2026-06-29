from __future__ import annotations

import importlib
import json
import threading
from typing import Literal

import networkx as nx
from src.dagbuilder import build_dag
from src.executor import StepPhase, run_workflow
from src.registry import Context, StepRegistry, WorkflowSpec
from src.ui.discovery import WorkflowDefinition, get_workflow, list_workflow_names
from src.ui.store import StepStatus, StepView, WorkflowStore

_EVAL_OK: StepPhase = "eval_pass"

PHASE_LABELS: dict[StepPhase, str] = {
    "start": "started",
    "complete": "completed",
    _EVAL_OK: "eval passed",
    "eval_retry": "eval retry",
    "eval_fail": "eval failed",
    "failure_handled": "failure handled",
    "error": "failed",
}

PHASE_STATUS: dict[StepPhase, StepStatus] = {
    "start": "running",
    "complete": "completed",
    _EVAL_OK: "running",
    "eval_retry": "running",
    "eval_fail": "eval_failed",
    "failure_handled": "handled",
    "error": "failed",
}

CASCADE_PHASES: frozenset[StepPhase] = frozenset({"eval_fail", "failure_handled"})


def _step_views(spec: WorkflowSpec) -> list[StepView]:
    return [
        StepView(
            name=step.step_name,
            caller=step.caller,
            eval=step.eval or (step.evals[0] if step.evals else None),
            evals=step.resolved_evals(),
            max_model_turns=step.max_model_turns,
            on_failure=step.on_failure,
            depends_on=list(step.depends_on),
        )
        for step in spec.steps
    ]


def _format_output(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, indent=2, default=str)
    except TypeError:
        return repr(value)


def _report_from_context(definition: WorkflowDefinition, ctx: Context) -> str | None:
    if definition.report_key is None:
        return None
    value = ctx.data.get(definition.report_key)
    if value is None and definition.report_key == "render_research_pdf":
        formatted = ctx.data.get("format_research_report")
        return str(formatted) if formatted is not None else None
    return str(value) if value is not None else None


def _pdf_from_context(ctx: Context) -> tuple[str | None, str | None]:
    payload = ctx.data.get("render_research_pdf")
    if isinstance(payload, dict):
        path = payload.get("path")
        url = payload.get("download_url")
        return (
            str(path) if path is not None else None,
            str(url) if url is not None else None,
        )
    pdf = ctx.data.get("pdf_report")
    if isinstance(pdf, dict):
        return (
            str(pdf.get("path")) if pdf.get("path") else None,
            str(pdf.get("download_url")) if pdf.get("download_url") else None,
        )
    return None, None


class WorkflowService:
    def __init__(self, store: WorkflowStore) -> None:
        self.store = store

    def start_run(self, name: str) -> str:
        definition = get_workflow(name)
        run = self.store.create_run(name, _step_views(definition.spec))
        thread = threading.Thread(
            target=self._execute,
            args=(run.workflow_id, definition),
            daemon=True,
        )
        thread.start()
        return run.workflow_id

    def _execute(self, workflow_id: str, definition: WorkflowDefinition) -> None:
        spec = definition.spec
        step_meta = {step.step_name: step for step in spec.steps}

        try:
            self.store.set_status(workflow_id, "running")
            importlib.import_module(definition.task_module)

            registry = StepRegistry()
            registry.load_workflow(spec)
            graph = build_dag(registry.all())
            ctx = Context(data={**definition.default_context, "run_id": workflow_id})

            def on_step(
                step_name: str,
                phase: StepPhase,
                error_detail: str | None = None,
            ) -> None:
                meta = step_meta.get(step_name)
                detail = PHASE_LABELS[phase]
                if phase == "eval_fail" and meta and meta.eval:
                    detail = f"eval failed ({meta.eval})"
                elif phase == "failure_handled" and meta and meta.on_failure:
                    suffix = f": {error_detail}" if error_detail else ""
                    detail = f"handled by {meta.on_failure}{suffix}"
                elif phase == "eval_pass" and error_detail:
                    detail = f"eval passed ({error_detail})"
                elif phase == "eval_retry":
                    suffix = f": {error_detail}" if error_detail else ""
                    detail = f"model turn retry{suffix}"

                output = None
                if phase == "complete":
                    output = _format_output(ctx.get_shared(step_name))

                self.store.set_step_status(workflow_id, step_name, PHASE_STATUS[phase])
                self.store.record_notify(
                    workflow_id,
                    step_name,
                    phase,
                    detail=detail,
                    output=output,
                )

                if phase in CASCADE_PHASES:
                    for downstream in nx.descendants(graph, step_name):
                        self.store.set_step_status(workflow_id, downstream, "skipped")
                        self.store.record_notify(
                            workflow_id,
                            downstream,
                            "inherited_skip",
                            detail="skipped (upstream branch did not pass)",
                        )

            def on_batch(
                wave_index: int,
                steps: list[str],
                event: Literal["start", "end"],
            ) -> None:
                self.store.record_wave(
                    workflow_id,
                    wave_index,
                    steps,
                    event=event,
                )

            ctx = run_workflow(
                graph,
                ctx,
                max_workers=definition.max_workers,
                on_step=on_step,
                on_batch=on_batch,
            )
            pdf_path, pdf_url = _pdf_from_context(ctx)
            self.store.finish(
                workflow_id,
                status="completed",
                report=_report_from_context(definition, ctx),
                pdf_path=pdf_path,
                pdf_download_url=pdf_url,
            )
        except Exception as exc:
            self.store.finish(workflow_id, status="failed", error=str(exc))
