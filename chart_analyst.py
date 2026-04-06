"""
AI-generated chart descriptions for the PDF report.

Calls Claude Haiku with only text data (summary stats) — no images are
sent to the API — keeping the cost to a fraction of a cent per report.
Falls back to hardcoded templates if the API is unavailable.
"""
import logging
import os

logger = logging.getLogger(__name__)

CHART_CONTEXTS = {
    "candlestick":         "OHLCV candlestick chart showing open, high, low and close prices with volume bars",
    "price_ma":            "line chart of closing price overlaid with 20, 50 and 200-day moving averages",
    "cumulative_return":   "line chart of cumulative percentage return from the start of the period",
    "drawdown":            "area chart showing the percentage drawdown from the rolling peak price",
    "monthly_returns":     "heatmap of monthly returns with green for positive and red for negative months",
    "summary_stats_table": "table of key financial metrics",
}

# Simple in-memory cache — avoids duplicate API calls when the same
# report is regenerated (e.g. Send Now triggered twice in a session).
_cache: dict = {}

_UNICODE_REPLACEMENTS = {
    "\u2014": "-",    # em dash
    "\u2013": "-",    # en dash
    "\u2018": "'",    # left single quote
    "\u2019": "'",    # right single quote
    "\u201c": '"',    # left double quote
    "\u201d": '"',    # right double quote
    "\u2026": "...",  # ellipsis
    "\u00a0": " ",    # non-breaking space
}


def _sanitise(text: str) -> str:
    for char, replacement in _UNICODE_REPLACEMENTS.items():
        text = text.replace(char, replacement)
    return text


def analyse_chart(chart_type: str, symbol: str, name: str, summary_stats: dict) -> str:
    """Return a 2-3 sentence AI description for a chart.

    Uses the chart type and summary statistics as context; no image is
    sent.  Falls back to a template string if the API call fails.
    """
    cache_key = f"{symbol}_{chart_type}"
    if cache_key in _cache:
        logger.info("Chart analysis cache hit for %s", cache_key)
        return _cache[cache_key]

    chart_context = CHART_CONTEXTS.get(chart_type, "financial chart")

    stats_text = "\n".join([
        f"- Total return: {summary_stats.get('total_return_pct', 'N/A')}%",
        f"- Annualised return: {summary_stats.get('annualised_return_pct', 'N/A')}%",
        f"- Volatility: {summary_stats.get('volatility_pct', 'N/A')}%",
        f"- Sharpe ratio: {summary_stats.get('sharpe_ratio', 'N/A')}",
        f"- Max drawdown: {summary_stats.get('max_drawdown_pct', 'N/A')}%",
        f"- Best day: {summary_stats.get('best_day_pct', 'N/A')}%",
        f"- Worst day: {summary_stats.get('worst_day_pct', 'N/A')}%",
        f"- Period: {summary_stats.get('start_date', '')} to {summary_stats.get('end_date', '')}",
    ])

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        message = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=150,
            system=(
                "You are a concise financial analyst writing brief chart "
                "descriptions for a financial report. Write exactly 2-3 "
                "sentences. Be specific — reference actual values from the "
                "stats provided. Focus on the most important insight the "
                "chart reveals. Do not use bullet points. Do not repeat "
                "the chart title. Do not add disclaimers or caveats. "
                "Write in plain, professional English."
            ),
            messages=[{
                "role": "user",
                "content": (
                    f"Write a 2-3 sentence description for the {chart_context} "
                    f"of {name} ({symbol}).\n\n"
                    f"Key statistics:\n{stats_text}"
                ),
            }],
        )
        result = _sanitise(message.content[0].text.strip())
        logger.info("AI analysis generated for %s / %s", symbol, chart_type)
    except Exception as exc:
        logger.warning("Anthropic API failed for %s/%s: %s. Using fallback.", symbol, chart_type, exc)
        result = _fallback_description(chart_type, symbol, summary_stats)

    _cache[cache_key] = result
    return result


def _fallback_description(chart_type: str, symbol: str, summary_stats: dict) -> str:
    total    = summary_stats.get("total_return_pct", "N/A")
    drawdown = summary_stats.get("max_drawdown_pct", "N/A")
    vol      = summary_stats.get("volatility_pct", "N/A")
    sharpe   = summary_stats.get("sharpe_ratio", "N/A")
    templates = {
        "candlestick": (
            f"The candlestick chart shows the price history of {symbol} over the selected period. "
            f"The asset delivered a total return of {total}% with an annualised volatility of {vol}%."
        ),
        "price_ma": (
            f"The moving average chart shows the trend structure of {symbol}. "
            f"A total return of {total}% was recorded over the period."
        ),
        "cumulative_return": (
            f"{symbol} delivered a cumulative return of {total}% over the selected period. "
            f"The chart shows how returns accumulated over time relative to the starting price."
        ),
        "drawdown": (
            f"The maximum drawdown for {symbol} was {drawdown}%, representing the largest "
            f"peak-to-trough decline in the period. "
            f"This metric reflects the downside risk experienced by a buy-and-hold investor."
        ),
        "monthly_returns": (
            f"The monthly returns heatmap reveals the distribution of gains and losses for "
            f"{symbol} across the period. "
            f"Annualised volatility of {vol}% reflects the consistency of these monthly outcomes."
        ),
        "summary_stats_table": (
            f"{symbol} achieved a Sharpe ratio of {sharpe} over the period, indicating the "
            f"risk-adjusted return relative to volatility of {vol}%."
        ),
    }
    return templates.get(
        chart_type,
        f"This chart shows the financial performance of {symbol} over the selected period.",
    )
