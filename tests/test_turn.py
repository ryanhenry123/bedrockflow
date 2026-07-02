from orchflow.evals.context import Context
from orchflow.evals.turn import Turn
from orchflow.providers.aws.bedrockruntime import cache_point, text_block


def test_cached_initial_message():
    turn = Turn(1, [], [])
    msgs = turn.build(initial="Write a memo.", cache_initial=True)
    assert msgs[0]["content"][0] == text_block("Write a memo.")
    assert msgs[0]["content"][1] == cache_point()


def test_retry_keeps_cache_on_initial():
    prior = [{"role": "assistant", "content": [{"text": "draft"}]}]
    turn = Turn(2, prior, ["fix sizing"])
    msgs = turn.build(initial="Write a memo.", cache_initial=True)
    assert msgs[0]["content"][1] == cache_point()
    assert len(msgs) == 3
