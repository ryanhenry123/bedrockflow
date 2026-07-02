from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

from tqdm import tqdm

from orchflow.envconfig import get_settings
from orchflow.evals.context import Context
from orchflow.evals.turn import Turn
from orchflow.evals.verdict import EvalFn, EvalVerdict, run_panel
from orchflow.providers.aws.bedrockruntime import ConverseResult, assistant_message


class EvalFailed(Exception):
    def __init__(self, result: ConverseResult):
        self.result = result
        super().__init__("eval panel returned FAIL")


class MaxTurnsExceeded(Exception):
    def __init__(self, result: ConverseResult, *, max_turns: int):
        self.result = result
        self.max_turns = max_turns
        super().__init__(f"exceeded max_turns={max_turns}")


@dataclass
class EvalLoopResult:
    result: ConverseResult
    turns: int
    ctx: Context


def run_with_evals(
    call: Callable[[Turn], ConverseResult],
    evals: Sequence[EvalFn],
    *,
    ctx: Context | dict[str, Any] | None = None,
    max_turns: int = 3,
    name: str | None = None,
) -> EvalLoopResult:
    ctx = Context(ctx or {})
    messages: list[dict[str, Any]] = []
    last: ConverseResult | None = None
    settings = get_settings()
    label = name or "eval loop"
    pbar = tqdm(
        range(1, max_turns + 1),
        total=max_turns,
        desc=label,
        unit="turn",
        disable=not settings.visible_turns,
    )
    for turn in pbar:
        pbar.set_postfix_str("calling model...", refresh=False)
        last = call(Turn(turn, messages, ctx.feedback_items))
        messages.append(assistant_message(last.text))
        verdict, reasons = run_panel(evals, ctx, last)
        pbar.set_postfix(verdict=verdict.value)
        if verdict is EvalVerdict.OK:
            return EvalLoopResult(result=last, turns=turn, ctx=ctx)
        if verdict is EvalVerdict.FAIL:
            raise EvalFailed(last)
        ctx.set_feedback(reasons)
        if settings.visible_turns and reasons:
            pbar.write("  retry: " + "; ".join(reasons))
        if turn == max_turns:
            raise MaxTurnsExceeded(last, max_turns=max_turns)
    raise RuntimeError("unreachable")
