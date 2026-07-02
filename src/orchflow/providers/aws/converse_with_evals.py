from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from orchflow.evals.context import Context
from orchflow.evals.runwithevals import EvalLoopResult, run_with_evals
from orchflow.evals.verdict import EvalFn
from orchflow.providers.aws.bedrockruntime import (
    InferenceConfig,
    converse,
)

InitialFn = Callable[[Context], str]


def _resolve_initial(initial: str | InitialFn, ctx: Context) -> str:
    return initial(ctx) if callable(initial) else initial


def converse_with_evals(
    model_id: str,
    initial: str | InitialFn,
    evals: Sequence[EvalFn],
    *,
    ctx: Context | dict[str, Any] | None = None,
    system: str | list[dict[str, Any]] | None = None,
    max_turns: int = 3,
    name: str | None = None,
    inference_config: InferenceConfig | None = None,
    max_tokens: int | None = None,
    temperature: float | None = None,
    top_p: float | None = None,
    stop_sequences: list[str] | None = None,
    tool_config: dict[str, Any] | None = None,
    guardrail_config: dict[str, Any] | None = None,
    additional_model_request_fields: dict[str, Any] | None = None,
    prompt_variables: dict[str, Any] | None = None,
    additional_model_response_field_paths: list[str] | None = None,
    request_metadata: dict[str, str] | None = None,
    performance_config: dict[str, Any] | None = None,
    service_tier: dict[str, Any] | None = None,
    output_config: dict[str, Any] | None = None,
    client: Any | None = None,
    **kwargs: Any,
) -> EvalLoopResult:
    """Call Bedrock Converse with an eval panel; owns message threading on retries."""
    ctx = Context(ctx or {})

    def call(turn):
        return converse(
            model_id,
            turn.build(initial=_resolve_initial(initial, ctx)),
            system=system,
            inference_config=inference_config,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stop_sequences=stop_sequences,
            tool_config=tool_config,
            guardrail_config=guardrail_config,
            additional_model_request_fields=additional_model_request_fields,
            prompt_variables=prompt_variables,
            additional_model_response_field_paths=additional_model_response_field_paths,
            request_metadata=request_metadata,
            performance_config=performance_config,
            service_tier=service_tier,
            output_config=output_config,
            client=client,
            **kwargs,
        )

    return run_with_evals(
        call,
        evals,
        ctx=ctx,
        max_turns=max_turns,
        name=name,
    )
