import re

from orchflow.evals.verdict import EvalVerdict
from orchflow.providers.aws.bedrockruntime import ConverseResult

REQUIRED_SECTIONS = (
    "## Verdict",
    "## Trades",
    "## Triggers",
    "## Thesis",
    "## Invalidation",
)


def _text(result: ConverseResult) -> str:
    return result.text.strip()


def _words(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def _section(text: str, heading: str) -> str:
    if heading not in text:
        return ""
    block = text.split(heading, 1)[1]
    nxt = re.search(r"\n## ", block)
    return block[: nxt.start()] if nxt else block


def eval_content_filtered(_ctx, result) -> EvalVerdict:
    if result.stop_reason == "content_filtered":
        return EvalVerdict.FAIL
    return EvalVerdict.OK


def eval_not_truncated(ctx, result) -> EvalVerdict:
    if result.stop_reason == "max_tokens":
        ctx.feedback("output truncated; shorten prose but keep all 5 sections complete")
        return EvalVerdict.RETRY
    return EvalVerdict.OK


def eval_structure(_ctx, result) -> EvalVerdict:
    text = _text(result)
    missing = [s for s in REQUIRED_SECTIONS if s not in text]
    if missing:
        _ctx.feedback(f"add sections: {', '.join(missing)}")
        return EvalVerdict.RETRY
    return EvalVerdict.OK


def eval_verdict_actionable(ctx, result) -> EvalVerdict:
    block = _section(_text(result), "## Verdict")
    if not re.search(
        r"\b(hedge|reduce|trim|cut|add|initiate|watch|avoid|hold|flat)\b",
        block,
        re.I,
    ):
        ctx.feedback(
            "## Verdict must state a clear desk action (hedge/reduce/add/watch/etc.)"
        )
        return EvalVerdict.RETRY
    return EvalVerdict.OK


def eval_sized_trades(ctx, result) -> EvalVerdict:
    block = _section(_text(result), "## Trades")
    if not re.search(r"\bbps\b|% of NAV|max (loss|premium)", block, re.I):
        ctx.feedback(
            "## Trades: size at least one leg in bps NAV or % with max loss/premium"
        )
        return EvalVerdict.RETRY
    trades = re.findall(r"^\d+\.", block, re.MULTILINE)
    if len(trades) < ctx.get("min_trades", 1):
        ctx.feedback(f"list at least {ctx.get('min_trades', 1)} numbered trade")
        return EvalVerdict.RETRY
    return EvalVerdict.OK


def eval_triggers(ctx, result) -> EvalVerdict:
    block = _section(_text(result), "## Triggers")
    rows = [ln for ln in block.splitlines() if ln.strip().startswith("|")]
    if len(rows) < 4:
        ctx.feedback(
            "## Triggers: table with Signal | Level | Action and at least 2 data rows"
        )
        return EvalVerdict.RETRY
    if not re.search(r"action", block, re.I):
        ctx.feedback("trigger table must include an Action column")
        return EvalVerdict.RETRY
    return EvalVerdict.OK


def eval_brevity(ctx, result) -> EvalVerdict:
    n = _words(_text(result))
    cap = ctx.get("max_words", 600)
    if n > cap:
        ctx.feedback(f"cut to {cap} words or fewer (currently {n})")
        return EvalVerdict.RETRY
    floor = ctx.get("min_words", 100)
    if n < floor:
        ctx.feedback(f"add detail to reach ~{floor}+ words (currently {n})")
        return EvalVerdict.RETRY
    return EvalVerdict.OK


def eval_recency(ctx, result) -> EvalVerdict:
    start, end = ctx.get("evidence_years", (2024, 2026))
    if not re.search(
        rf"\b({'|'.join(str(y) for y in range(start, end + 1))})\b", _text(result)
    ):
        ctx.feedback(f"anchor to {start}-{end} data or events")
        return EvalVerdict.RETRY
    return EvalVerdict.OK


def eval_invalidation(ctx, result) -> EvalVerdict:
    block = _section(_text(result), "## Invalidation")
    if _words(block) < 15:
        ctx.feedback("## Invalidation: 2-3 concrete falsifiers (what proves us wrong)")
        return EvalVerdict.RETRY
    return EvalVerdict.OK


DRAFT_EVALS = [
    eval_content_filtered,
    eval_not_truncated,
    eval_structure,
    eval_verdict_actionable,
    eval_sized_trades,
    eval_triggers,
    eval_brevity,
    eval_recency,
    eval_invalidation,
]
