import os
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Literal

import networkx as nx
from utils.log import get_logger
from src.dagbuilder import ready_steps
from src.models.eval import EvalVerdict, run_eval_panel
from src.registry import Context, Step

LOGGER = get_logger(__file__)

StepPhase = Literal[
    "start",
    "complete",
    "eval_pass",
    "eval_retry",
    "eval_fail",
    "failure_handled",
    "error",
]
StepListener = Callable[..., None]
BatchListener = Callable[[int, list[str], Literal["start", "end"]], None]


@dataclass(frozen=True, slots=True)
class _StepOutcome:
    name: str
    status: Literal["completed", "eval_fail", "failure_handled", "error"]
    error: Exception | None = None
    eval_passed: bool = False
    model_turns: int = 1


def _default_workers(batch_size: int) -> int:
    cpu = os.cpu_count() or 4
    return max(1, min(batch_size, cpu))


def _execute_step(
    name: str,
    step: Step,
    ctx: Context,
    on_step: StepListener | None = None,
) -> _StepOutcome:
    try:
        result: object | None = None
        model_turns = 0

        while model_turns < step.max_model_turns:
            model_turns += 1
            ctx.set_shared(f"{name}__turn", model_turns)

            result = step.caller_func(ctx)
            ctx.set_shared(name, result)

            if not step.eval_funcs:
                return _StepOutcome(name, "completed", model_turns=model_turns)

            verdict, retry_reasons = run_eval_panel(step.eval_funcs, ctx, result, name)

            if verdict is EvalVerdict.OK:
                for eval_func in step.eval_funcs:
                    _notify(on_step, name, "eval_pass", eval_func.__name__)
                return _StepOutcome(
                    name,
                    "completed",
                    eval_passed=True,
                    model_turns=model_turns,
                )

            if verdict is EvalVerdict.FAIL:
                return _StepOutcome(name, "eval_fail", model_turns=model_turns)

            # RETRY — another model turn if budget remains
            detail = "; ".join(retry_reasons) if retry_reasons else "revision requested"
            _notify(on_step, name, "eval_retry", detail)
            if model_turns >= step.max_model_turns:
                ctx.set_shared(
                    f"{name}__eval_failure_reason",
                    f"exhausted {step.max_model_turns} model turn(s): {detail}",
                )
                return _StepOutcome(name, "eval_fail", model_turns=model_turns)

        return _StepOutcome(name, "eval_fail", model_turns=model_turns)
    except Exception as exc:
        if step.failure_func:
            step.failure_func(ctx, exc)
            return _StepOutcome(name, "failure_handled", error=exc)
        LOGGER.error("Step %s failed with no failure handler", name)
        return _StepOutcome(name, "error", exc)


def _notify(
    on_step: StepListener | None,
    name: str,
    phase: StepPhase,
    detail: str | None = None,
) -> None:
    if on_step is not None:
        on_step(name, phase, detail)


def _apply_outcome(
    g: nx.DiGraph,
    outcome: _StepOutcome,
    completed: set[str],
    skipped: set[str],
    on_step: StepListener | None = None,
) -> None:
    if outcome.status == "completed":
        completed.add(outcome.name)
        _notify(on_step, outcome.name, "complete")
        return

    if outcome.status == "eval_fail":
        skipped.add(outcome.name)
        skipped.update(nx.descendants(g, outcome.name))
        _notify(on_step, outcome.name, "eval_fail")
        return

    if outcome.status == "failure_handled":
        skipped.add(outcome.name)
        skipped.update(nx.descendants(g, outcome.name))
        _notify(
            on_step,
            outcome.name,
            "failure_handled",
            str(outcome.error) if outcome.error else None,
        )
        return

    if outcome.error is not None:
        _notify(on_step, outcome.name, "error")
        raise outcome.error


def _run_batch_serial(
    g: nx.DiGraph,
    batch: list[str],
    ctx: Context,
    completed: set[str],
    skipped: set[str],
    on_step: StepListener | None = None,
) -> None:
    for name in batch:
        _notify(on_step, name, "start")
        step: Step = g.nodes[name]["step"]
        _apply_outcome(
            g, _execute_step(name, step, ctx, on_step), completed, skipped, on_step
        )


def _run_batch_parallel(
    g: nx.DiGraph,
    batch: list[str],
    ctx: Context,
    completed: set[str],
    skipped: set[str],
    max_workers: int,
    on_step: StepListener | None = None,
) -> None:
    for name in batch:
        _notify(on_step, name, "start")

    workers = max(1, min(max_workers, len(batch)))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        outcomes = pool.map(
            lambda name: _execute_step(name, g.nodes[name]["step"], ctx, on_step=None),
            batch,
        )
        for outcome in outcomes:
            _apply_outcome(g, outcome, completed, skipped, on_step)


def run_workflow(
    g: nx.DiGraph,
    ctx: Context,
    *,
    max_workers: int | None = None,
    on_step: StepListener | None = None,
    on_batch: BatchListener | None = None,
) -> Context:
    completed: set[str] = set()
    skipped: set[str] = set()
    wave_index = 0

    while len(completed) + len(skipped) < g.number_of_nodes():
        batch = [n for n in ready_steps(g, completed) if n not in skipped]
        if not batch:
            err = "Deadlock: no runnable steps."
            LOGGER.error(err)
            raise RuntimeError(err)

        if on_batch is not None:
            on_batch(wave_index, batch, "start")

        if len(batch) == 1 or max_workers == 1:
            _run_batch_serial(g, batch, ctx, completed, skipped, on_step)
        else:
            workers = (
                max_workers if max_workers is not None else _default_workers(len(batch))
            )
            _run_batch_parallel(g, batch, ctx, completed, skipped, workers, on_step)

        if on_batch is not None:
            on_batch(wave_index, batch, "end")
        wave_index += 1

    return ctx
