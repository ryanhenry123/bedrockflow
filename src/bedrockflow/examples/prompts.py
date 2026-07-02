from bedrockflow.examples.evals import REQUIRED_SECTIONS, SECTION_SPEC

SYSTEM = (
    "You write trade memos for portfolio managers with 90 seconds to read. "
    "Lead with verdict and sized trades. No sell-side tone, no long citations, "
    "no 'PMs should assess' disclaimers. Every line supports a trade or a trigger."
)


def draft_prompt(ctx) -> str:
    cap = ctx.get("max_words", 600)
    spec = "\n".join(
        f"{heading} — {SECTION_SPEC[heading]}" for heading in REQUIRED_SECTIONS
    )
    return (
        f"Topic: {ctx['topic']}\n"
        f"Horizon: {ctx.get('horizon', '3-6 months')}\n\n"
        f"Write a TRADE MEMO (max {cap} words) with exactly these sections:\n"
        f"{spec}\n"
        "Be terse. No reference list."
    )
