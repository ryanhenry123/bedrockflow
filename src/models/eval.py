from __future__ import annotations

from collections.abc import Callable, Sequence
from enum import StrEnum
from typing import Any


class EvalVerdict(StrEnum):
    OK = "ok"
    RETRY = "retry"
    FAIL = "fail"


EvalResult = bool | EvalVerdict | None


def normalize_eval_result(result: EvalResult) -> EvalVerdict:
    if result is None:
        return EvalVerdict.FAIL
    if isinstance(result, bool):
        return EvalVerdict.OK if result else EvalVerdict.FAIL
    return result


def run_eval_panel(
    eval_funcs: Sequence[Callable[[Any, object], EvalResult]],
    ctx: Any,
    result: object,
    step_name: str,
) -> tuple[EvalVerdict, list[str]]:
    """Run evals in order. FAIL wins; else RETRY if any; else OK."""
    retry_reasons: list[str] = []
    saw_retry = False

    for eval_func in eval_funcs:
        verdict = normalize_eval_result(eval_func(ctx, result))
        if verdict is EvalVerdict.FAIL:
            return EvalVerdict.FAIL, retry_reasons

        if verdict is EvalVerdict.RETRY:
            saw_retry = True
            reason = ctx.get_shared(f"{step_name}__retry_reason")
            if isinstance(reason, str) and reason.strip():
                retry_reasons.append(reason.strip())
            ctx.set_shared(f"{step_name}__retry_reason", None)

    if saw_retry:
        reasons = retry_reasons or ["revision requested"]
        ctx.set_shared(f"{step_name}__feedback", reasons)
        return EvalVerdict.RETRY, reasons

    return EvalVerdict.OK, []
