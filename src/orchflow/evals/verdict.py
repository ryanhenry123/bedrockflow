from __future__ import annotations

from collections.abc import Callable, Sequence
from enum import StrEnum
from typing import Any

from pydantic.types import T


class EvalVerdict(StrEnum):
    OK = "ok"
    RETRY = "retry"
    FAIL = "fail"


EvalFn = Callable[[Any, Any], "EvalVerdict | bool | None"]


def normalize(result: EvalVerdict | bool | None) -> EvalVerdict:
    if result is None:
        return EvalVerdict.FAIL
    if isinstance(result, bool):
        return EvalVerdict.OK if result else EvalVerdict.FAIL
    return result


def run_panel(
    evals: Sequence[EvalFn], ctx: Any, result: Any
) -> tuple[EvalVerdict, list[str]]:
    reasons: list[str] = []
    saw_retry = False
    for fn in evals:
        verdict = normalize(fn(ctx, result))
        if verdict is EvalVerdict.FAIL:
            return EvalVerdict.FAIL, reasons
        elif verdict is EvalVerdict.RETRY:
            saw_retry = True
            if msg := ctx.pop_feedback():
                reasons.append(msg)
    if saw_retry:
        return EvalVerdict.RETRY, reasons or ["revision requested"]
    return EvalVerdict.OK, []
