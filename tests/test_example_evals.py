from orchflow.evals.context import Context
from orchflow.evals.verdict import EvalVerdict, run_panel
from orchflow.examples.evals import DRAFT_EVALS
from conftest import MockResult

GOOD_MEMO = """## Verdict
Reduce short-vol beta; add tail hedge over 3-6m. Crowding rebuilt post Aug-2024 spike.

## Trades
1. VIX 25/40 call spread 3mo — 12 bps NAV max premium, roll if VIX < 18.
2. Trim short SPX 1m 25d put — 8 bps NAV notional reduction.

## Triggers
| Signal | Level | Action |
| --- | --- | --- |
| VIX 1m | > 28 for 3d | Add 5 bps NAV hedge |
| CFTC net short | +10% WoW | Flag crowding |

## Thesis
- Aug 2024 VIX spike to 65 shows crowding (2024).
- Positioning rebuilt into 2025; dealers still short gamma in calm tape.
- IVP still positive — incentive to sell vol persists until a vol shock.

## Invalidation
- VIX net short positioning falls 20% without a spike — crowding thesis dead.
- Clean VIX 25-35 event with no dealer stress or skew bid — tail hedge unnecessary.
- Realized vol under implied for 60d with IVP < 30 — resume vol selling.
"""


def test_trade_memo_eval_panel_passes_fixture():
    ctx = Context(
        evidence_years=(2024, 2026),
        max_words=600,
        min_words=100,
        min_trades=1,
    )
    verdict, reasons = run_panel(DRAFT_EVALS, ctx, MockResult(GOOD_MEMO))
    assert verdict is EvalVerdict.OK
    assert reasons == []


def test_trade_memo_eval_panel_fails_missing_sections():
    ctx = Context(evidence_years=(2024, 2026))
    verdict, reasons = run_panel(
        DRAFT_EVALS, ctx, MockResult("## Verdict\nHedge now.\n")
    )
    assert verdict is EvalVerdict.RETRY
    assert any("sections" in r for r in reasons)
