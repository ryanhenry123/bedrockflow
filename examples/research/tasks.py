"""Research report workflows with multi-turn Bedrock eval loops."""

from __future__ import annotations

import re
from typing import Any

from src.models.eval import EvalVerdict
from src.models.model_turn import ModelTurnSession
from src.models.roles import Role
from src.registerfuncs import register
from src.registry import Context

DEFAULT_MODEL_ID = "amazon.nova-lite-v1:0"
DRAFT_STEP = "draft_research_report"

_MOCK_DRAFTS = [
    "Volatility is interesting.",
    (
        "## Overview\n"
        "2025 saw systematic vol selling compress premia across SPX and single-name books.\n"
        "## Findings\n"
        "Crowding raised tail risk into macro shocks."
    ),
    (
        "## Overview\n"
        "Systematic volatility selling remained crowded through 2025 and into 2026, "
        "compressing SPX and single-name variance premia.\n"
        "## Recent Evidence\n"
        "2024-2026 dealer gamma positioning amplified short-vol drawdowns during liquidity gaps.\n"
        "## Implications\n"
        "Carry is attractive but left-tail convexity is underpriced when multiple pods run similar books.\n"
        "Risk committees should monitor gross notional overlap and shock scenarios quarterly.\n"
        "## References\n"
        "- BIS Quarterly Review (2025): Volatility risk premium dynamics\n"
        "- JP Morgan Derivatives Strategy (2026): Crowded vol selling monitor\n"
        "- AQR Capital Management (2024): Tail risk in alternative risk premia"
    ),
]


def _word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def _mock_draft(ctx: Context, topic: str, model_id: str) -> dict[str, Any]:
    session = ModelTurnSession.read(ctx, DRAFT_STEP, max_turns=4)
    idx = min(session.turn - 1, len(_MOCK_DRAFTS) - 1)
    if ctx.data.get("mock_response_text"):
        text = str(ctx.data["mock_response_text"])
    else:
        text = _MOCK_DRAFTS[idx]
    return {
        "text": text,
        "topic": topic,
        "model_id": model_id,
        "turn": session.turn,
        "input_tokens": 120,
        "output_tokens": max(1, _word_count(text)),
    }


def _live_draft(
    ctx: Context,
    topic: str,
    model_id: str,
    *,
    session: ModelTurnSession,
    feedback: list[str],
) -> dict[str, Any]:
    from modelprovider.bedrockruntimeclient import BedrockRuntimeClass
    from modelprovider.runtime.types import (
        ConverseRequest,
        InferenceConfig,
        assistant_message,
        system_block,
        user_message,
    )

    base_prompt = (
        f"Topic: {topic}\n"
        "Write a concise institutional research note with sections:\n"
        "## Overview\n## Recent Evidence\n## Implications\n## References\n"
        "Ground claims in 2024-2026 market structure and cite at least two sources."
    )
    messages: list[dict[str, Any]] = [user_message(base_prompt)]
    if session.is_retry and feedback:
        prior = session.prior_result(ctx)
        prior_text = str(prior.get("text", "")) if isinstance(prior, dict) else ""
        if prior_text:
            messages.append(assistant_message(prior_text))
        messages.append(
            user_message(
                "Revise the research note. Address:\n- " + "\n- ".join(feedback)
            )
        )

    request = ConverseRequest(
        modelId=model_id,
        system=[
            system_block(
                "You are a senior quantitative research analyst at a multi-strategy fund. "
                "Write rigorous, citation-aware notes."
            )
        ],
        messages=messages,
        inferenceConfig=InferenceConfig(maxTokens=768, temperature=0.2),
    )
    result = BedrockRuntimeClass().converse(request)
    return {
        "text": result.text.strip(),
        "topic": topic,
        "model_id": model_id,
        "turn": session.turn,
        "input_tokens": result.usage.input_tokens,
        "output_tokens": result.usage.output_tokens,
    }


@register("load_research_brief", Role.CALLER)
def load_research_brief(ctx: Context) -> dict[str, str]:
    topic = str(
        ctx.data.get(
            "topic",
            "Systematic volatility selling crowding and tail risk (2024-2026)",
        )
    )
    model_id = str(ctx.data.get("model_id", DEFAULT_MODEL_ID))
    ctx.data["topic"] = topic
    ctx.data["model_id"] = model_id
    return {"topic": topic, "model_id": model_id}


@register("draft_research_report", Role.CALLER)
def draft_research_report(ctx: Context) -> dict[str, Any]:
    brief = ctx.data["load_research_brief"]
    topic = str(brief["topic"])
    model_id = str(brief["model_id"])
    session = ModelTurnSession.read(ctx, DRAFT_STEP, max_turns=4)
    feedback = session.feedback(ctx)

    if ctx.data.get("mock_bedrock"):
        payload = _mock_draft(ctx, topic, model_id)
    else:
        payload = _live_draft(ctx, topic, model_id, session=session, feedback=feedback)

    ctx.data["research_draft"] = payload
    return payload


@register("eval_report_structure", Role.EVAL)
def eval_report_structure(ctx: Context, result: object) -> EvalVerdict:
    if not isinstance(result, dict):
        return EvalVerdict.FAIL
    text = str(result.get("text", ""))
    headings = re.findall(r"^##\s+\S+", text, flags=re.MULTILINE)
    if len(headings) < 3:
        ModelTurnSession.request_retry(
            ctx,
            DRAFT_STEP,
            "add markdown section headings (## Overview, ## Recent Evidence, ## Implications, ## References)",
        )
        return EvalVerdict.RETRY
    return EvalVerdict.OK


@register("eval_report_recency", Role.EVAL)
def eval_report_recency(ctx: Context, result: object) -> EvalVerdict:
    if not isinstance(result, dict):
        return EvalVerdict.FAIL
    text = str(result.get("text", ""))
    if not re.search(r"\b(2024|2025|2026)\b", text):
        ModelTurnSession.request_retry(
            ctx,
            DRAFT_STEP,
            "anchor the note to 2024-2026 evidence and data",
        )
        return EvalVerdict.RETRY
    return EvalVerdict.OK


@register("eval_report_references", Role.EVAL)
def eval_report_references(ctx: Context, result: object) -> EvalVerdict:
    if not isinstance(result, dict):
        return EvalVerdict.FAIL
    text = str(result.get("text", ""))
    if not re.search(r"(?im)^##\s+(references|sources)\b", text):
        ModelTurnSession.request_retry(
            ctx,
            DRAFT_STEP,
            "include a ## References section with at least two cited sources",
        )
        return EvalVerdict.RETRY
    refs = re.findall(r"(?m)^-\s+\S+", text)
    if len(refs) < 2:
        ModelTurnSession.request_retry(
            ctx,
            DRAFT_STEP,
            "list at least two bullet citations under References",
        )
        return EvalVerdict.RETRY
    return EvalVerdict.OK


@register("eval_report_depth", Role.EVAL)
def eval_report_depth(ctx: Context, result: object) -> EvalVerdict:
    if not isinstance(result, dict):
        return EvalVerdict.FAIL
    text = str(result.get("text", ""))
    min_words = int(ctx.data.get("min_report_words", 80))
    words = _word_count(text)
    if words < min_words:
        ModelTurnSession.request_retry(
            ctx,
            DRAFT_STEP,
            f"expand analysis to at least {min_words} words (currently {words})",
        )
        return EvalVerdict.RETRY
    return EvalVerdict.OK


@register("handle_research_failure", Role.FAILURE)
def handle_research_failure(ctx: Context, exc: Exception) -> None:
    ctx.data["research_error"] = str(exc)
    ctx.data["research_error_type"] = type(exc).__name__


@register("format_research_report", Role.CALLER)
def format_research_report(ctx: Context) -> str:
    brief = ctx.data["load_research_brief"]
    draft = ctx.data["draft_research_report"]
    topic = brief["topic"]
    turns = draft.get("turn", 1)
    tokens = draft.get("output_tokens", 0)
    header = f"# Research Report: {topic}\n\n"
    footer = f"\n\n---\n_generated in {turns} model turn(s), {tokens} output tokens_"
    return header + str(draft["text"]).strip() + footer


@register("render_research_pdf", Role.CALLER)
def render_research_pdf(ctx: Context) -> dict[str, str]:
    from src.reports.pdf_builder import build_research_pdf

    brief = ctx.data["load_research_brief"]
    narrative = str(ctx.data["format_research_report"])
    run_id = str(ctx.data.get("run_id", "local"))
    path = build_research_pdf(
        topic=str(brief["topic"]),
        narrative=narrative,
        run_id=run_id,
    )
    payload = {
        "path": str(path),
        "filename": path.name,
        "download_url": f"/reports/{path.stem}.pdf",
    }
    ctx.data["pdf_report"] = payload
    return payload
