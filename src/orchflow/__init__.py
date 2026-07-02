"""Bedrock-native eval loop: call a model, run quality gates, retry with feedback."""

from orchflow.evals.context import Context
from orchflow.evals.runwithevals import (
    EvalFailed,
    EvalLoopResult,
    MaxTurnsExceeded,
    run_with_evals,
)
from orchflow.evals.turn import Turn
from orchflow.evals.types import EvalResult
from orchflow.evals.verdict import EvalFn, EvalVerdict, run_panel

__all__ = [
    "Context",
    "EvalFailed",
    "EvalFn",
    "EvalLoopResult",
    "EvalResult",
    "EvalVerdict",
    "MaxTurnsExceeded",
    "Turn",
    "run_panel",
    "run_with_evals",
]


def main() -> None:
    from orchflow.examples.trade_memo import main as run_example

    run_example()
