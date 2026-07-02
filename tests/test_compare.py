from bedrockflow.evals.context import Context
from bedrockflow.evals.verdict import EvalVerdict
from bedrockflow.providers.aws.converse_with_evals import compare_models
from conftest import MockResult


def test_compare_models_ranks_pass_fail(monkeypatch):
    calls: list[str] = []

    def fake_converse(model_id, messages, **kwargs):
        calls.append(model_id)
        if "bad" in model_id:
            return MockResult("x", output_tokens=1)
        return MockResult("long enough passing answer here", output_tokens=9)

    monkeypatch.setattr(
        "bedrockflow.providers.aws.converse_with_evals.converse",
        fake_converse,
    )

    def min_len(ctx, result):
        if len(result.text.strip()) < 10:
            ctx.feedback("too short")
            return EvalVerdict.RETRY
        return EvalVerdict.OK

    min_len.__eval_name__ = "min_len"

    rows = compare_models(
        ["good-model", "bad-model"],
        initial="question",
        evals=[min_len],
        ctx=Context(),
        max_turns=2,
    )
    assert rows[0].passed is True
    assert rows[1].passed is False
    assert rows[0].model_id == "good-model"
