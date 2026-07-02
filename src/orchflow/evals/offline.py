from __future__ import annotations

import importlib
import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from orchflow.evals.context import Context
from orchflow.evals.types import EvalResult
from orchflow.evals.verdict import EvalFn, EvalVerdict, run_panel


@dataclass(frozen=True)
class TextResult:
    text: str
    stop_reason: str = "end_turn"


def load_panel(spec: str) -> Sequence[EvalFn]:
    """Load an eval panel from ``module.path:ATTRIBUTE``."""
    if ":" not in spec:
        raise ValueError(f"panel must be module.path:ATTRIBUTE, got {spec!r}")
    module_name, attr = spec.rsplit(":", 1)
    module = importlib.import_module(module_name)
    panel = getattr(module, attr)
    if not isinstance(panel, Sequence):
        raise TypeError(f"{spec} is not a sequence of eval functions")
    return panel


def eval_text(
    text: str,
    evals: Sequence[EvalFn],
    *,
    ctx: Context | dict | None = None,
    stop_reason: str = "end_turn",
) -> tuple[EvalVerdict, list[str]]:
    result: EvalResult = TextResult(text=text, stop_reason=stop_reason)
    return run_panel(evals, Context(ctx or {}), result)


@dataclass(frozen=True)
class FixtureReport:
    path: Path
    verdict: EvalVerdict
    reasons: list[str]


def eval_fixture(
    path: Path,
    evals: Sequence[EvalFn],
    *,
    ctx: Context | dict | None = None,
    stop_reason: str = "end_turn",
) -> FixtureReport:
    text = path.read_text(encoding="utf-8")
    verdict, reasons = eval_text(text, evals, ctx=ctx, stop_reason=stop_reason)
    return FixtureReport(path=path, verdict=verdict, reasons=reasons)


def eval_paths(
    paths: Sequence[Path],
    evals: Sequence[EvalFn],
    *,
    ctx: Context | dict | None = None,
    stop_reason: str = "end_turn",
) -> list[FixtureReport]:
    reports: list[FixtureReport] = []
    for path in paths:
        if path.is_dir():
            files = sorted(path.glob("*.md")) + sorted(path.glob("*.txt"))
            reports.extend(
                eval_fixture(f, evals, ctx=ctx, stop_reason=stop_reason) for f in files
            )
        else:
            reports.append(eval_fixture(path, evals, ctx=ctx, stop_reason=stop_reason))
    return reports


def format_report(report: FixtureReport) -> str:
    lines = [f"{report.path}: {report.verdict.value}"]
    for reason in report.reasons:
        lines.append(f"  - {reason}")
    return "\n".join(lines)


def run_eval_cli(
    paths: Sequence[str | Path],
    *,
    panel: str,
    ctx: Context | dict | None = None,
    stop_reason: str = "end_turn",
) -> int:
    evals = load_panel(panel)
    resolved = [Path(p) for p in paths]
    reports = eval_paths(resolved, evals, ctx=ctx, stop_reason=stop_reason)
    failed = False
    for report in reports:
        print(format_report(report))
        if report.verdict is not EvalVerdict.OK:
            failed = True
    return 1 if failed else 0


def parse_ctx_json(raw: str | None) -> Context | None:
    if not raw:
        return None
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("ctx JSON must be an object")
    return Context(data)
