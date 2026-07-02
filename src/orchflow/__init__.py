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


def converse_with_evals(*args, **kwargs):
    from orchflow.providers.aws.converse_with_evals import converse_with_evals as impl

    return impl(*args, **kwargs)


__all__ = [
    "Context",
    "EvalFailed",
    "EvalFn",
    "EvalLoopResult",
    "EvalResult",
    "EvalVerdict",
    "MaxTurnsExceeded",
    "Turn",
    "converse_with_evals",
    "run_panel",
    "run_with_evals",
]
