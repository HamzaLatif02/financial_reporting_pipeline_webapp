"""
Comparison analysis: runs both pipelines and computes correlation,
aligned cumulative returns, and side-by-side metric winners.
"""
import logging

import pandas as pd

from analysis import run_analysis

logger = logging.getLogger(__name__)


def _correlation_label(r: float) -> str:
    if r >= 0.8:    return "Strong positive"
    if r >= 0.5:    return "Moderate positive"
    if r >= 0.2:    return "Weak positive"
    if r >= -0.2:   return "Uncorrelated"
    if r >= -0.5:   return "Weak negative"
    if r >= -0.8:   return "Moderate negative"
    return "Strong negative"


def _winner(key: str, val_a, val_b) -> str:
    """Return 'a', 'b', or 'tie'. volatility_pct: lower is better; all others: higher is better."""
    if val_a is None or val_b is None:
        return "tie"
    lower_better = {"volatility_pct"}
    if key in lower_better:
        if val_a < val_b:   return "a"
        if val_b < val_a:   return "b"
    else:
        if val_a > val_b:   return "a"
        if val_b > val_a:   return "b"
    return "tie"


def run_comparison(config_a: dict, config_b: dict) -> dict:
    """Run full comparison analysis for two assets. Returns a results dict."""
    symbol_a = config_a["symbol"]
    symbol_b = config_b["symbol"]

    logger.info("Running comparison: %s vs %s", symbol_a, symbol_b)

    analysis_a = run_analysis(config_a)
    analysis_b = run_analysis(config_b)

    # ── Align price series on common date index ────────────────────────────────
    df_a = analysis_a["price_series"]
    df_b = analysis_b["price_series"]

    close_a = df_a["close"] if "close" in df_a.columns else df_a["Close"]
    close_b = df_b["close"] if "close" in df_b.columns else df_b["Close"]

    combined = pd.DataFrame({
        symbol_a: close_a,
        symbol_b: close_b,
    }).dropna()

    overlap_days = len(combined)
    logger.info("Overlapping trading days: %d", overlap_days)

    if overlap_days < 10:
        raise ValueError(
            f"Insufficient overlapping data between {symbol_a} and {symbol_b} for comparison."
        )

    # ── Cumulative returns from first overlapping date ─────────────────────────
    cum_returns = (combined / combined.iloc[0] - 1) * 100

    # ── Correlation of daily returns ───────────────────────────────────────────
    daily_rets = combined.pct_change().dropna()
    corr_matrix = daily_rets.corr()
    pearson_r = round(float(corr_matrix.loc[symbol_a, symbol_b]), 4)
    corr_label = _correlation_label(pearson_r)

    # ── Side-by-side metric winners ────────────────────────────────────────────
    a_stats = analysis_a.get("summary_stats") or {}
    b_stats = analysis_b.get("summary_stats") or {}

    metric_keys = [
        "total_return_pct",
        "annualised_return_pct",
        "volatility_pct",
        "sharpe_ratio",
        "max_drawdown_pct",
        "best_day_pct",
        "worst_day_pct",
    ]

    metrics = {}
    for key in metric_keys:
        val_a = a_stats.get(key)
        val_b = b_stats.get(key)
        metrics[key] = {
            "a":      val_a,
            "b":      val_b,
            "winner": _winner(key, val_a, val_b),
        }

    # ── Serialise DataFrames ───────────────────────────────────────────────────
    def _to_records(df: pd.DataFrame) -> list:
        r = df.reset_index()
        r.columns = ["date"] + list(r.columns[1:])
        r["date"] = r["date"].astype(str)
        return r.to_dict("records")

    return {
        "symbol_a":        symbol_a,
        "symbol_b":        symbol_b,
        "name_a":          config_a["name"],
        "name_b":          config_b["name"],
        "period":          config_a["period"],
        "interval":        config_a["interval"],
        "overlap_days":    overlap_days,
        "correlation":     {"value": pearson_r, "label": corr_label},
        "metrics":         metrics,
        "cum_returns":     _to_records(cum_returns),
        "combined_prices": _to_records(combined),
        "analysis_a":      analysis_a,
        "analysis_b":      analysis_b,
    }
