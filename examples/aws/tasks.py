"""Bedrock-backed step functions for aws_risk_summary workflows."""

from __future__ import annotations

from typing import Any

from src.models.roles import Role
from src.registerfuncs import register
from src.registry import Context

DEFAULT_MODEL_ID = "amazon.nova-lite-v1:0"


def _mock_converse(ctx: Context, model_id: str, user_text: str) -> dict[str, Any]:
    if ctx.data.get("force_bedrock_error"):
        raise RuntimeError(f"forced bedrock failure for model {model_id!r}")

    text = str(
        ctx.data.get(
            "mock_response_text",
            "Primary risk is gap risk and liquidity stress if the thesis breaks on AAPL.",
        )
    )
    return {
        "text": text,
        "stop_reason": "end_turn",
        "input_tokens": 24,
        "output_tokens": max(1, len(text) // 4),
        "model_id": model_id,
        "prompt_preview": user_text[:120],
    }


def _live_converse(model_id: str, symbol: str, thesis: str) -> dict[str, Any]:
    from modelprovider.bedrockruntimeclient import BedrockRuntimeClass
    from modelprovider.runtime.types import ConverseRequest, InferenceConfig

    user_text = (
        f"Symbol: {symbol}\n"
        f"Thesis: {thesis}\n"
        "In 2-3 sentences, state the primary risk to this position."
    )
    request = ConverseRequest.single_turn(
        model_id,
        user_text,
        system_text="You are a portfolio risk analyst. Be concise and direct.",
        inference_config=InferenceConfig(maxTokens=128, temperature=0.0),
    )
    result = BedrockRuntimeClass().converse(request)
    return {
        "text": result.text.strip(),
        "stop_reason": str(result.stop_reason),
        "input_tokens": result.usage.input_tokens,
        "output_tokens": result.usage.output_tokens,
        "model_id": model_id,
        "prompt_preview": user_text[:120],
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
    user_text = (
        f"Symbol: {symbol}\n"
        f"Thesis: {thesis}\n"
        "In 2-3 sentences, state the primary risk to this position."
    )

    if ctx.data.get("mock_bedrock"):
        payload = _mock_converse(ctx, model_id, user_text)
    else:
        payload = _live_converse(model_id, symbol, thesis)

    ctx.data["bedrock_summary"] = payload
    return payload


@register("validate_summary", Role.EVAL)
def validate_summary(ctx: Context, result: object) -> bool:
    if not isinstance(result, dict):
        ctx.data["eval_failure_reason"] = "summary result was not a dict"
        return False

    text = result.get("text")
    if not isinstance(text, str) or not text.strip():
        ctx.data["eval_failure_reason"] = "empty model response"
        return False

    min_chars = ctx.data.get("min_response_chars", 20)
    if isinstance(min_chars, int) and len(text.strip()) < min_chars:
        ctx.data["eval_failure_reason"] = (
            f"response shorter than required {min_chars} characters"
        )
        return False

    if result.get("stop_reason") == "content_filtered":
        ctx.data["eval_failure_reason"] = "content filtered by model"
        return False

    return True


@register("handle_bedrock_failure", Role.FAILURE)
def handle_bedrock_failure(ctx: Context, exc: Exception) -> None:
    ctx.data["bedrock_error"] = str(exc)
    ctx.data["bedrock_error_type"] = type(exc).__name__


@register("format_memo", Role.CALLER)
def format_memo(ctx: Context) -> str:
    symbol = ctx.data["load_thesis"]["symbol"]
    summary = ctx.data["summarize_risk"]
    return f"{symbol} RISK MEMO " f"({summary['output_tokens']} tok): {summary['text']}"
