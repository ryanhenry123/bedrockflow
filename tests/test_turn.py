from orchflow.evals.context import Context
from orchflow.evals.turn import Turn


def test_first_turn_is_initial_prompt_only():
    turn = Turn(1, [], [])
    msgs = turn.build(initial="Write a memo.")
    assert len(msgs) == 1
    assert msgs[0]["role"] == "user"
    assert msgs[0]["content"][0]["text"] == "Write a memo."


def test_retry_includes_initial_latest_draft_and_feedback():
    prior = [{"role": "assistant", "content": [{"text": "draft v1"}]}]
    turn = Turn(2, prior, ["fix sizing", "add triggers"])
    msgs = turn.build(initial="Write a memo.")
    assert len(msgs) == 3
    assert msgs[0]["content"][0]["text"] == "Write a memo."
    assert msgs[1] == prior[-1]
    assert "fix sizing" in msgs[2]["content"][0]["text"]
    assert "Revise your full memo" in msgs[2]["content"][0]["text"]
