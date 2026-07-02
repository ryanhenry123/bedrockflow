from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Any

from pydantic import BaseModel

from bedrockflow.evals.checks import (
    fail_on_filter,
    min_length,
    require_json,
    require_sections,
    stop_not_truncated,
    word_count,
)
from bedrockflow.evals.verdict import EvalFn


def markdown_sections(
    *headings: str,
    min_words: int | None = None,
    max_words: int | None = None,
    min_chars: int | None = None,
) -> list[EvalFn]:
    """Starter panel for markdown documents with required headings."""
    panel: list[EvalFn] = [
        fail_on_filter(),
        stop_not_truncated(name="not_truncated"),
        require_sections(*headings, name="structure"),
    ]
    if min_words is not None or max_words is not None:
        panel.append(word_count(min=min_words, max=max_words, name="brevity"))
    if min_chars is not None:
        panel.append(min_length(min_chars, name="min_length"))
    return panel


def json_object(
    *,
    required_keys: Sequence[str] | None = None,
    schema: type[BaseModel] | None = None,
) -> list[EvalFn]:
    """Starter panel for JSON object outputs."""
    return [
        fail_on_filter(),
        stop_not_truncated(name="not_truncated"),
        require_json(required_keys=required_keys, schema=schema, name="json"),
    ]


def no_preamble() -> EvalFn:
    """Reject outputs that start with conversational filler."""
    from bedrockflow.evals.checks import matches

    return matches(
        r"(?m)^(##|\{|```)",
        msg="start with content (heading, JSON, or fenced block) — no preamble",
        name="no_preamble",
    )


def csv_table(*, min_rows: int = 2, min_cols: int = 2) -> EvalFn:
    """Require a markdown pipe table with minimum shape."""
    from bedrockflow.evals.types import EvalResult
    from bedrockflow.evals.verdict import EvalVerdict

    def check(ctx: Any, result: EvalResult) -> EvalVerdict:
        rows = [
            ln.strip() for ln in result.text.splitlines() if ln.strip().startswith("|")
        ]
        non_sep = [r for r in rows if not re.match(r"^\|[\s\-:|]+\|$", r)]
        if len(non_sep) < min_rows + 1:
            ctx.feedback(f"include a markdown table with at least {min_rows} data rows")
            return EvalVerdict.RETRY
        cols = [c for c in non_sep[0].split("|") if c.strip()]
        if len(cols) < min_cols:
            ctx.feedback(f"table needs at least {min_cols} columns")
            return EvalVerdict.RETRY
        return EvalVerdict.OK

    check.__eval_name__ = "csv_table"  # type: ignore[attr-defined]
    return check
