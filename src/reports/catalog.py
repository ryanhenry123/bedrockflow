from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StatSeries:
    label: str
    x: tuple[str, ...]
    y: tuple[float, ...]
    ylabel: str
    chart_type: str = "line"


@dataclass(frozen=True, slots=True)
class ReportDataset:
    slug: str
    title: str
    subtitle: str
    kpis: tuple[tuple[str, str], ...]
    series: tuple[StatSeries, ...]
    table_title: str
    table_headers: tuple[str, ...]
    table_rows: tuple[tuple[str, ...], ...]
    methodology: str
    examples: tuple[str, ...]


VOL_SELLING = ReportDataset(
    slug="vol_selling",
    title="Systematic Volatility Selling",
    subtitle="Crowding, carry, and tail-risk dynamics (2024–2026)",
    kpis=(
        ("Avg. 1M VRP", "4.8 vol pts"),
        ("Crowding z-score", "2.1σ"),
        ("Aug-2025 gap loss", "-18.4%"),
        ("Hit rate (carry)", "71%"),
    ),
    series=(
        StatSeries(
            "Variance risk premium (1M, vol pts)",
            ("2024Q1", "2024Q3", "2025Q1", "2025Q3", "2026Q1"),
            (5.2, 4.1, 3.6, 2.9, 4.8),
            "VRP (vol)",
        ),
        StatSeries(
            "Short-vol fund net exposure index",
            ("Jan-24", "Jul-24", "Jan-25", "Jul-25", "Jan-26"),
            (62.0, 78.0, 91.0, 88.0, 84.0),
            "Index level",
        ),
    ),
    table_title="Tail-event loss distribution (Aug-2025 liquidity gap)",
    table_headers=("Percentile", "1D P&L", "Observations", "Notes"),
    table_rows=(
        ("P50", "-2.1%", "142", "Typical gap day"),
        ("P95", "-11.6%", "142", "Dealer gamma flip"),
        ("P99", "-18.4%", "142", "Crowding unwind"),
        ("Max", "-24.7%", "142", "Vol-of-vol spike"),
    ),
    methodology=(
        "VRP computed as 1M implied SPX variance minus realized variance (21-day). "
        "Crowding z-score vs. 2015–2023 pod exposure panel. Loss distribution from "
        "a synthetic short-straddle basket calibrated to pod disclosures."
    ),
    examples=(
        "Rolling 63-day correlation of VRP to MOVE index: 0.58 (2025).",
        "Granger causality: crowding index → next-week VRP compression (p<0.05).",
    ),
)

MOMENTUM = ReportDataset(
    slug="momentum",
    title="Cross-Sectional Momentum Decay",
    subtitle="Signal erosion, turnover, and transaction-cost drag (2024–2026)",
    kpis=(
        ("12-1M spread (ann.)", "6.2%"),
        ("IC (1M forward)", "0.04"),
        ("Avg. book turnover", "186%"),
        ("Cost-adjusted Sharpe", "0.42"),
    ),
    series=(
        StatSeries(
            "Cumulative factor return (12-1M)",
            ("2024", "2024H2", "2025", "2025H2", "2026Q1"),
            (1.0, 1.04, 1.07, 1.05, 1.062),
            "Growth of $1",
            "line",
        ),
        StatSeries(
            "Information coefficient by horizon",
            ("1M", "3M", "6M", "12M"),
            (0.04, 0.06, 0.05, 0.03),
            "IC",
            "bar",
        ),
    ),
    table_title="Decile spread statistics (US equities, 2024–2026)",
    table_headers=("Metric", "Value", "Benchmark", "Commentary"),
    table_rows=(
        ("Mean spread", "6.2%", "8.1% (2010–19)", "Compression post-2022"),
        ("t-stat (NW)", "2.4", ">2.0", "Still significant"),
        ("Max drawdown", "-14.3%", "-22% (2020)", "Shallower tail"),
        ("Turnover", "186%", "120% hist.", "Crowded rebalances"),
    ),
    methodology=(
        "Universe: top 1,500 US names by ADV. Signal: 12-month return skipping last "
        "month. Portfolios value-weighted within deciles. IC measured Spearman on "
        "1-month forward returns with Newey-West t-stats."
    ),
    examples=(
        "Fama-MacBeth regression: momentum premium 0.52%/month (SE 0.21).",
        "Turnover penalty: each 100% turnover ≈ 85 bps drag on net spread.",
    ),
)

RATES_BETA = ReportDataset(
    slug="rates_beta",
    title="Rates Curve & Equity Beta Regimes",
    subtitle="2s10s inversion episodes and conditional market sensitivity (2024–2026)",
    kpis=(
        ("Current 2s10s", "+42 bps"),
        ("Equity beta (inverted)", "1.38"),
        ("Equity beta (steep)", "0.92"),
        ("R² (regime switch)", "0.61"),
    ),
    series=(
        StatSeries(
            "US 2s10s yield spread (bps)",
            ("2024Q1", "2024Q3", "2025Q1", "2025Q3", "2026Q1"),
            (-48.0, -12.0, 18.0, 35.0, 42.0),
            "Spread (bps)",
        ),
        StatSeries(
            "Rolling 60D SPX beta to 10Y yield changes",
            ("2024H1", "2024H2", "2025H1", "2025H2", "2026Q1"),
            (1.45, 1.22, 1.05, 0.98, 0.92),
            "Beta",
        ),
    ),
    table_title="Conditional equity beta by curve regime",
    table_headers=("Regime", "2s10s", "Beta", "Sample (days)"),
    table_rows=(
        ("Inverted", "< 0 bps", "1.38", "218"),
        ("Flat", "0–50 bps", "1.08", "164"),
        ("Steep", "> 50 bps", "0.92", "97"),
        ("All", "—", "1.12", "479"),
    ),
    methodology=(
        "Beta estimated via rolling 60-day OLS of SPX daily returns on 10Y yield "
        "changes. Regimes classified by same-day 2s10s level. Sample: Jan-2024–Mar-2026."
    ),
    examples=(
        "Chow test confirms structural break in beta at first re-steepening (p<0.01).",
        "Macro PCA factor 1 explains 73% of cross-regime beta variation.",
    ),
)

CATALOG: tuple[ReportDataset, ...] = (VOL_SELLING, MOMENTUM, RATES_BETA)


def resolve_dataset(topic: str) -> ReportDataset:
    normalized = topic.lower()
    if "momentum" in normalized or "cross-sectional" in normalized:
        return MOMENTUM
    if "rate" in normalized or "curve" in normalized or "beta" in normalized:
        return RATES_BETA
    return VOL_SELLING


def list_catalog_slugs() -> list[str]:
    return [item.slug for item in CATALOG]
