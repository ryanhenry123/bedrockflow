from orchflow.examples.evals import REQUIRED_SECTIONS

SYSTEM = (
    "You write trade memos for portfolio managers with 90 seconds to read. "
    "Lead with verdict and sized trades. No sell-side tone, no long citations, "
    "no 'PMs should assess' disclaimers. Every line supports a trade or a trigger."
)


def draft_prompt(ctx) -> str:
    cap = ctx.get("max_words", 600)
    return (
        f"Topic: {ctx['topic']}\n"
        f"Horizon: {ctx.get('horizon', '3-6 months')}\n\n"
        f"Write a TRADE MEMO (max {cap} words) with exactly these sections:\n"
        + "\n".join(REQUIRED_SECTIONS)
        + "\n\n"
        "## Verdict — one line stance + horizon.\n"
        "## Trades — numbered; each with structure, sizing (bps NAV or %), max loss/premium.\n"
        "## Triggers — markdown table: Signal | Level | Action (at least 2 rows).\n"
        "## Thesis — max 3 bullets tying to 2024-2026 evidence.\n"
        "## Invalidation — 2-3 falsifiers only.\n"
        "Be terse. No reference list."
    )
