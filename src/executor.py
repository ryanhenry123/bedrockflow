import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Literal

import networkx as nx
from utils.log import get_logger
from src.dagbuilder import ready_steps
from src.registry import Context, Step

LOGGER = get_logger(__file__)


@dataclass(frozen=True, slots=True)
class _StepOutcome:
    name: str
    status: Literal["completed", "skipped", "error"]
    error: Exception | None = None


def _default_workers(batch_size: int) -> int:
    cpu = os.cpu_count() or 4
    return max(1, min(batch_size, cpu))


def _execute_step(name: str, step: Step, ctx: Context) -> _StepOutcome:
    try:
        result = step.caller_func(ctx)
        ctx.set_shared(name, result)

        if step.eval_func and not step.eval_func(ctx, result):
            return _StepOutcome(name, "skipped")

        return _StepOutcome(name, "completed")
    except Exception as exc:
        if step.failure_func:
            step.failure_func(ctx, exc)
            return _StepOutcome(name, "skipped")
        LOGGER.error("Step %s failed with no failure handler", name)
        return _StepOutcome(name, "error", exc)


def _apply_outcome(
    g: nx.DiGraph,
    outcome: _StepOutcome,
    completed: set[str],
    skipped: set[str],
) -> None:
    if outcome.status == "completed":
        completed.add(outcome.name)
        return

    if outcome.status == "skipped":
        skipped.add(outcome.name)
        skipped.update(nx.descendants(g, outcome.name))
        return

    if outcome.error is not None:
        raise outcome.error


def _run_batch_serial(
    g: nx.DiGraph,
    batch: list[str],
    ctx: Context,
    completed: set[str],
    skipped: set[str],
) -> None:
    for name in batch:
        step: Step = g.nodes[name]["step"]
        _apply_outcome(g, _execute_step(name, step, ctx), completed, skipped)


def _run_batch_parallel(
    g: nx.DiGraph,
    batch: list[str],
    ctx: Context,
    completed: set[str],
    skipped: set[str],
    max_workers: int,
) -> None:
    workers = max(1, min(max_workers, len(batch)))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        outcomes = pool.map(
            lambda name: _execute_step(name, g.nodes[name]["step"], ctx),
            batch,
        )
        for outcome in outcomes:
            _apply_outcome(g, outcome, completed, skipped)


def run_workflow(
    g: nx.DiGraph,
    ctx: Context,
    *,
    max_workers: int | None = None,
) -> Context:
    completed: set[str] = set()
    skipped: set[str] = set()

    while len(completed) + len(skipped) < g.number_of_nodes():
        batch = [n for n in ready_steps(g, completed) if n not in skipped]
        if not batch:
            err = "Deadlock: no runnable steps."
            LOGGER.error(err)
            raise RuntimeError(err)

        if len(batch) == 1 or max_workers == 1:
            _run_batch_serial(g, batch, ctx, completed, skipped)
            continue

        workers = (
            max_workers if max_workers is not None else _default_workers(len(batch))
        )
        _run_batch_parallel(g, batch, ctx, completed, skipped, workers)

    return ctx
