from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from bedrockflow.evals.runwithevals import EvalLoopResult, TurnTrace
from bedrockflow.evals.verdict import EvalStep, EvalVerdict


def _enum_value(value: Any) -> Any:
    return value.value if isinstance(value, EvalVerdict) else value


def step_to_dict(step: EvalStep) -> dict[str, Any]:
    return {
        "name": step.name,
        "verdict": step.verdict.value,
        "reasons": list(step.reasons),
    }


def turn_trace_to_dict(trace: TurnTrace) -> dict[str, Any]:
    steps = trace.steps
    step_dicts = [step_to_dict(s) if isinstance(s, EvalStep) else s for s in steps]
    return {
        "turn": trace.turn,
        "verdict": trace.verdict.value,
        "reasons": list(trace.reasons),
        "output_tokens": trace.output_tokens,
        "input_tokens": trace.input_tokens,
        "cache_read_input_tokens": trace.cache_read_input_tokens,
        "cache_write_input_tokens": trace.cache_write_input_tokens,
        "steps": step_dicts,
    }


def token_summary(trace: list[TurnTrace]) -> dict[str, int]:
    summary = {
        "output_tokens": 0,
        "input_tokens": 0,
        "cache_read_input_tokens": 0,
        "cache_write_input_tokens": 0,
    }
    for row in trace:
        for key in summary:
            val = getattr(row, key, None)
            if isinstance(val, int):
                summary[key] += val
    return summary


def run_result_to_dict(
    out: EvalLoopResult,
    *,
    model_id: str | None = None,
    name: str | None = None,
    passed: bool = True,
    error: str | None = None,
) -> dict[str, Any]:
    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "name": name,
        "model_id": model_id,
        "passed": passed,
        "error": error,
        "turns": out.turns,
        "tokens": token_summary(out.trace),
        "trace": [turn_trace_to_dict(t) for t in out.trace],
        "text": out.result.text,
    }


def write_trace(path: Path | str, payload: dict[str, Any]) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return target


def write_run_artifact(
    path: Path | str,
    out: EvalLoopResult,
    *,
    model_id: str | None = None,
    name: str | None = None,
    passed: bool = True,
    error: str | None = None,
) -> Path:
    return write_trace(
        path,
        run_result_to_dict(
            out,
            model_id=model_id,
            name=name,
            passed=passed,
            error=error,
        ),
    )
