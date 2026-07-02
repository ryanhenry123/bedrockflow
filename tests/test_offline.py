from pathlib import Path

from orchflow.evals.context import Context
from orchflow.evals.offline import eval_fixture, eval_paths, load_panel
from orchflow.evals.verdict import EvalVerdict
from orchflow.examples.evals import DRAFT_EVALS

FIXTURES = Path(__file__).parent / "fixtures"
TRADE_CTX = {
    "evidence_years": (2024, 2026),
    "max_words": 600,
    "min_words": 100,
    "min_trades": 1,
}


def test_load_panel():
    panel = load_panel("orchflow.examples.evals:DRAFT_EVALS")
    assert panel is DRAFT_EVALS


def test_good_fixture_passes():
    report = eval_fixture(
        FIXTURES / "good_memo.md",
        DRAFT_EVALS,
        ctx=TRADE_CTX,
    )
    assert report.verdict is EvalVerdict.OK
    assert report.reasons == []


def test_bad_fixture_fails_with_reasons():
    report = eval_fixture(
        FIXTURES / "bad_memo.md",
        DRAFT_EVALS,
        ctx=TRADE_CTX,
    )
    assert report.verdict is EvalVerdict.RETRY
    assert report.reasons


def test_eval_directory():
    reports = eval_paths([FIXTURES], DRAFT_EVALS, ctx=TRADE_CTX)
    assert len(reports) == 2
    by_name = {r.path.name: r for r in reports}
    assert by_name["good_memo.md"].verdict is EvalVerdict.OK
    assert by_name["bad_memo.md"].verdict is EvalVerdict.RETRY
