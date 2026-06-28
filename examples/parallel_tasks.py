"""Parallel portfolio tasks that merge results into shared context state."""

import time

from src.models.roles import Role
from src.registerfuncs import register
from src.registry import Context

_MOCK_PRICES: dict[str, list[float]] = {
    "AAPL": [150.0, 151.2, 149.8, 152.0],
    "MSFT": [410.5, 412.0, 409.25, 411.75],
}


@register("load_watchlist", Role.CALLER)
def load_watchlist(ctx: Context) -> list[str]:
    symbols = ctx.data.get("symbols", ["AAPL", "MSFT"])
    normalized = [str(symbol).upper() for symbol in symbols]
    ctx.set_shared("symbols", normalized)
    ctx.set_shared("quotes", {})
    return normalized


@register("fetch_aapl", Role.CALLER)
def fetch_aapl(ctx: Context) -> dict[str, float | int]:
    time.sleep(0.05)
    prices = _MOCK_PRICES["AAPL"]
    quote = {"count": len(prices), "avg": sum(prices) / len(prices)}
    ctx.merge_shared("quotes", {"AAPL": quote})
    return quote


@register("fetch_msft", Role.CALLER)
def fetch_msft(ctx: Context) -> dict[str, float | int]:
    time.sleep(0.05)
    prices = _MOCK_PRICES["MSFT"]
    quote = {"count": len(prices), "avg": sum(prices) / len(prices)}
    ctx.merge_shared("quotes", {"MSFT": quote})
    return quote


@register("aggregate_portfolio", Role.CALLER)
def aggregate_portfolio(ctx: Context) -> dict[str, float | int]:
    quotes = ctx.get_shared("quotes", {})
    if not isinstance(quotes, dict) or not quotes:
        raise ValueError("Shared quotes missing from parallel fetch steps")

    avgs = [quote["avg"] for quote in quotes.values()]
    return {
        "symbols": len(quotes),
        "avg": sum(avgs) / len(avgs),
        "total_ticks": sum(quote["count"] for quote in quotes.values()),
    }


@register("format_portfolio_report", Role.CALLER)
def format_portfolio_report(ctx: Context) -> str:
    summary = ctx.data["aggregate_portfolio"]
    symbols = ctx.get_shared("symbols", [])
    symbol_list = ",".join(symbols) if isinstance(symbols, list) else ""
    return (
        f"portfolio[{symbol_list}]: avg={summary['avg']:.2f} "
        f"over {summary['total_ticks']} ticks"
    )
