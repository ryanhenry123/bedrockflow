from pathlib import Path

from bedrockflow.evals.context import Context
from bedrockflow.evals.runwithevals import MaxTurnsExceeded
from bedrockflow.examples.models import MODEL
from bedrockflow.examples.runner import finish_run, handle_run_failure
from bedrockflow.examples.simple_evals import SIMPLE_EVALS
from bedrockflow.providers.aws.converse_with_evals import converse_with_evals

SYSTEM = (
    "Write concise markdown for busy readers. "
    "No preamble, no disclaimers, no filler."
)


def draft_prompt(ctx: Context) -> str:
    return (
        f"Topic: {ctx['topic']}\n\n"
        "Write a short markdown note with exactly:\n"
        "## Summary — 2-3 sentences.\n"
        "## Key Points — 3 bullet points.\n"
        f"Stay under {ctx.get('max_words', 200)} words."
    )


def run_simple_summary(ctx: Context, *, cache_initial: bool = False):
    return converse_with_evals(
        ctx.get("model_id", MODEL),
        initial=lambda c: draft_prompt(c),
        evals=SIMPLE_EVALS,
        ctx=ctx,
        system=SYSTEM,
        max_tokens=512,
        temperature=0.2,
        max_turns=3,
        name="simple_summary",
        cache_initial=cache_initial,
    )


def main(
    *,
    record: Path | None = None,
    trace: Path | None = None,
    cache_initial: bool = False,
) -> None:
    ctx = Context(
        topic="Why systematic vol selling builds tail risk in calm markets",
        max_words=200,
        min_words=30,
    )
    model_id = ctx.get("model_id", MODEL)
    try:
        out = run_simple_summary(ctx, cache_initial=cache_initial)
    except MaxTurnsExceeded as exc:
        handle_run_failure(
            exc,
            model_id=model_id,
            name="simple_summary",
            record=record,
            trace=trace,
        )
        raise SystemExit(1) from None
    finish_run(
        out,
        model_id=model_id,
        name="simple_summary",
        record=record,
        trace=trace,
    )


if __name__ == "__main__":
    main()
