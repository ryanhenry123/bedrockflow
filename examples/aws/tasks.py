"""Bedrock-backed step functions for aws_risk_summary workflows."""

from __future__ import annotations

from typing import Any

from src.models.eval import EvalVerdict
from src.models.model_turn import ModelTurnSession
from src.models.roles import Role
from src.registerfuncs import register
from src.registry import Context

DEFAULT_MODEL_ID = "amazon.nova-lite-v1:0"
STEP = "summarize_risk"


def _mock_converse(ctx: Context, model_id: str, user_text: str) -> dict[str, Any]:
    if ctx.data.get("force_bedrock_error"):
        raise RuntimeError(f"forced bedrock failure for model {model_id!r}")

    session = ModelTurnSession.read(ctx, STEP, max_turns=3)
    symbol = str(ctx.data.get("symbol", "AAPL")).upper()
    if session.is_retry:
        text = str(
            ctx.data.get(
                "mock_response_text",
                (
                    f"Primary risk to {symbol} is gap and liquidity stress if the "
                    "thesis breaks; size and hedge accordingly."
                ),
            )
        )
    else:
        text = str(ctx.data.get("mock_response_text", "Risk exists."))

    return {
        "text": text,
        "stop_reason": "end_turn",
        "input_tokens": 24,
        "output_tokens": max(1, len(text) // 4),
        "model_id": model_id,
        "turn": session.turn,
        "prompt_preview": user_text[:160],
    }


def _live_converse(
    ctx: Context,
    model_id: str,
    symbol: str,
    thesis: str,
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

    user_text = (
        f"Symbol: {symbol}\n"
        f"Thesis: {thesis}\n"
        "In 2-3 sentences, state the primary risk to this position."
    )
    messages: list[dict[str, Any]] = [user_message(user_text)]
    if session.is_retry and feedback:
        prior = session.prior_result(ctx)
        prior_text = ""
        if isinstance(prior, dict):
            prior_text = str(prior.get("text", ""))
        if prior_text:
            messages.append(assistant_message(prior_text))
        messages.append(
            user_message("Revise your answer addressing:\n- " + "\n- ".join(feedback))
        )

    request = ConverseRequest(
        modelId=model_id,
        system=[
            system_block("You are a portfolio risk analyst. Be concise and direct.")
        ],
        messages=messages,
        inferenceConfig=InferenceConfig(maxTokens=160, temperature=0.0),
    )
    result = BedrockRuntimeClass().converse(request)
    return {
        "text": result.text.strip(),
        "stop_reason": str(result.stop_reason),
        "input_tokens": result.usage.input_tokens,
        "output_tokens": result.usage.output_tokens,
        "model_id": model_id,
        "turn": session.turn,
        "prompt_preview": user_text[:160],
    }


@register("load_thesis", Role.CALLER)
def load_thesis(ctx: Context) -> dict[str, str]:
    symbol = str(ctx.data.get("symbol", "AAPL")).upper()
    thesis = str(ctx.data.get("thesis", "Long gamma into earnings"))
    model_id = str(ctx.data.get("model_id", DEFAULT_MODEL_ID))
    ctx.data["symbol"] = symbol
    ctx.data["thesis"] = thesis
    ctx.data["model_id"] = model_id
    return {"symbol": symbol, "thesis": thesis, "model_id": model_id}


@register("summarize_risk", Role.CALLER)
def summarize_risk(ctx: Context) -> dict[str, Any]:
    symbol = str(ctx.data["load_thesis"]["symbol"])
    thesis = str(ctx.data["load_thesis"]["thesis"])
    model_id = str(ctx.data["load_thesis"]["model_id"])
    session = ModelTurnSession.read(ctx, STEP, max_turns=3)
    feedback = session.feedback(ctx)
    user_text = (
        f"Symbol: {symbol}\n"
        f"Thesis: {thesis}\n"
        "In 2-3 sentences, state the primary risk to this position."
    )

    if ctx.data.get("mock_bedrock"):
        payload = _mock_converse(ctx, model_id, user_text)
    else:
        payload = _live_converse(
            ctx,
            model_id,
            symbol,
            thesis,
            session=session,
            feedback=feedback,
        )

    ctx.data["bedrock_summary"] = payload
    return payload


@register("eval_summary_nonempty", Role.EVAL)
def eval_summary_nonempty(ctx: Context, result: object) -> EvalVerdict:
    if not isinstance(result, dict):
        ModelTurnSession.request_retry(
            ctx, STEP, "response must be structured JSON from the model"
        )
        return EvalVerdict.RETRY
    text = result.get("text")
    if not isinstance(text, str) or not text.strip():
        ModelTurnSession.request_retry(ctx, STEP, "response text is empty")
        return EvalVerdict.RETRY
    if result.get("stop_reason") == "content_filtered":
        return EvalVerdict.FAIL
    return EvalVerdict.PASS


@register("eval_summary_length", Role.EVAL)
def eval_summary_length(ctx: Context, result: object) -> EvalVerdict:
    if not isinstance(result, dict):
        return EvalVerdict.FAIL
    text = str(result.get("text", ""))
    min_chars = ctx.data.get("min_response_chars", 40)
    if isinstance(min_chars, int) and len(text.strip()) < min_chars:
        ModelTurnSession.request_retry(
            ctx,
            STEP,
            f"expand to at least {min_chars} characters (got {len(text.strip())})",
        )
        return EvalVerdict.RETRY
    return EvalVerdict.PASS


@register("eval_summary_mentions_symbol", Role.EVAL)
def eval_summary_mentions_symbol(ctx: Context, result: object) -> EvalVerdict:
    if not isinstance(result, dict):
        return EvalVerdict.FAIL
    symbol = str(ctx.data.get("symbol", "")).upper()
    text = str(result.get("text", "")).upper()
    if symbol and symbol not in text:
        ModelTurnSession.request_retry(
            ctx, STEP, f"explicitly reference symbol {symbol}"
        )
        return EvalVerdict.RETRY
    return EvalVerdict.PASS


@register("handle_bedrock_failure", Role.FAILURE)
def handle_bedrock_failure(ctx: Context, exc: Exception) -> None:
    ctx.data["bedrock_error"] = str(exc)
    ctx.data["bedrock_error_type"] = type(exc).__name__


@register("format_memo", Role.CALLER)
def format_memo(ctx: Context) -> str:
    symbol = ctx.data["load_thesis"]["symbol"]
    summary = ctx.data["summarize_risk"]
    turns = summary.get("turn", 1)
    return (
        f"{symbol} RISK MEMO "
        f"({summary['output_tokens']} tok, {turns} turn(s)): {summary['text']}"
    )
