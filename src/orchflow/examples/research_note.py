from orchflow.evals.context import Context
from orchflow.evals.runwithevals import run_with_evals
from orchflow.providers.aws.bedrockruntime import converse
from orchflow.examples.evals import DRAFT_EVALS
from orchflow.examples.prompts import SYSTEM, draft_prompt
from orchflow.examples.models import MODEL


def draft_trade_memo(ctx: Context):
    brief = ctx["brief"]
    return run_with_evals(
        call=lambda turn: converse(
            ctx.get("model_id", MODEL),
            turn.build(initial=draft_prompt({**ctx, **brief})),
            system=SYSTEM,
            max_tokens=1500,
            temperature=0.2,
        ),
        evals=DRAFT_EVALS,
        ctx=ctx,
        max_turns=5,
        name="trade_memo",
    )


def load_brief(ctx: Context) -> dict:
    return {
        "topic": ctx.get(
            "topic",
            "Systematic vol selling crowding and tail risk (2024-2026)",
        ),
        "horizon": ctx.get("horizon", "3-6 months"),
        "model_id": ctx.get("model_id", MODEL),
    }


def main() -> None:
    ctx = Context(
        topic="Systematic vol selling crowding and tail risk (2024-2026)",
        evidence_years=(2024, 2026),
        max_words=600,
        min_words=100,
        min_trades=1,
    )
    ctx["brief"] = load_brief(ctx)
    out = draft_trade_memo(ctx)
    print(out.result.text)
    print(
        f"\n--- {out.turns} turn(s), {out.result.usage.output_tokens} output tokens ---"
    )


if __name__ == "__main__":
    main()
