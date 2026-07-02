from pathlib import Path

from orchflow.evals.context import Context
from orchflow.evals.verdict import EvalVerdict, run_panel
from orchflow.examples.evals import DRAFT_EVALS

FIXTURES = Path(__file__).parent / "fixtures"
TRADE_CTX = Context(
    evidence_years=(2024, 2026),
    max_words=600,
    min_words=100,
    min_trades=1,
)


def test_trade_memo_eval_panel_passes_fixture():
    text = (FIXTURES / "good_memo.md").read_text(encoding="utf-8")
    verdict, reasons = run_panel(DRAFT_EVALS, TRADE_CTX, _mock(text))
    assert verdict is EvalVerdict.OK
    assert reasons == []


def test_trade_memo_eval_panel_fails_missing_sections():
    verdict, reasons = run_panel(
        DRAFT_EVALS, TRADE_CTX, _mock("## Verdict\nHedge now.\n")
    )
    assert verdict is EvalVerdict.RETRY
    assert any("sections" in r for r in reasons)


def test_verdict_accepts_inflected_desk_actions():
    from orchflow.examples.evals import eval_verdict_actionable

    verdict = (
        "## Verdict\n"
        "Crowding extreme; **desk adds 95bps NAV in convexity hedges today**.\n"
    )
    ctx = Context()
    assert eval_verdict_actionable(ctx, _mock(verdict)) is EvalVerdict.OK


def _mock(text: str, stop: str = "end_turn"):
    from conftest import MockResult

    return MockResult(text, stop)
