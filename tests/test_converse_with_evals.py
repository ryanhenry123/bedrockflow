from orchflow.evals.context import Context
from orchflow.evals.verdict import EvalVerdict
from orchflow.providers.aws.bedrockruntime import ConverseResult, TokenUsage
from orchflow.providers.aws.converse_with_evals import converse_with_evals


def _result(text: str) -> ConverseResult:
    return ConverseResult(
        text=text,
        stop_reason="end_turn",
        usage=TokenUsage.model_validate(
            {"inputTokens": 1, "outputTokens": len(text.split()), "totalTokens": 2}
        ),
    )


def test_converse_with_evals_retries_until_ok(monkeypatch):
    prompts: list[list[dict]] = []

    def fake_converse(_model_id, messages, **_kwargs):
        prompts.append(messages)
        if len(prompts) == 1:
            return _result("short")
        return _result("This answer is long enough to pass the check easily.")

    monkeypatch.setattr(
        "orchflow.providers.aws.converse_with_evals.converse",
        fake_converse,
    )

    def eval_min_length(ctx, result) -> EvalVerdict:
        if len(result.text.strip()) < 20:
            ctx.feedback("answer in at least one full sentence")
            return EvalVerdict.RETRY
        return EvalVerdict.OK

    out = converse_with_evals(
        "us.anthropic.claude-sonnet-4-6",
        initial="What is 2+2?",
        evals=[eval_min_length],
        ctx=Context(),
        max_turns=3,
    )

    assert out.turns == 2
    assert len(out.result.text) >= 20
    assert len(prompts) == 2
    assert prompts[0] == [{"role": "user", "content": [{"text": "What is 2+2?"}]}]
    assert prompts[1][0]["role"] == "user"
    assert prompts[1][1]["role"] == "assistant"
    assert "full sentence" in prompts[1][2]["content"][0]["text"]
