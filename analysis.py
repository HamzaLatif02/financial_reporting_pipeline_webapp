import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

import cleaner
import db

logging.basicConfig(level=logging.INFO, format="%(levelname)s — %(message)s")
logger = logging.getLogger(__name__)


def _load_prices(config: dict) -> pd.DataFrame:
    """Load price data from DB, falling back to the cleaned CSV."""
    symbol = config["symbol"]
    try:
        df = db.query_prices(symbol)
        if not df.empty:
            logger.info("Loaded %d rows from DB for %s.", len(df), symbol)
            return df
    except Exception as exc:
        logger.warning("DB query failed for %s: %s", symbol, exc)

    logger.info("Falling back to cleaned CSV for %s.", symbol)
    return cleaner.load_clean(symbol)


def _load_info(symbol: str) -> dict:
    """Load the raw info JSON for a symbol, returning an empty dict if absent."""
    path = Path(f"data/raw/{symbol}_info.json")
    if path.exists():
        with open(path) as f:
            return json.load(f)
    logger.warning("No info JSON found for %s.", symbol)
    return {}


def _compute_summary_stats(df: pd.DataFrame) -> dict:
    """Compute key performance metrics from a cleaned price DataFrame."""
    close = df["close"] if "close" in df.columns else df["Close"]
    daily_ret = df["daily_return"] if "daily_return" in df.columns else df.get("daily_return")
    volume = df["volume"] if "volume" in df.columns else df.get("Volume")

    first_close = close.iloc[0]
    last_close = close.iloc[-1]
    total_return = (last_close - first_close) / first_close * 100

    start_date = df.index[0]
    end_date = df.index[-1]
    n_years = (end_date - start_date).days / 365.25
    annualised_return = ((1 + total_return / 100) ** (1 / n_years) - 1) * 100 if n_years > 0 else None

    vol = daily_ret.std() * np.sqrt(252) if daily_ret is not None else None
    sharpe = (annualised_return / vol) if (vol and vol != 0 and annualised_return is not None) else None

    # Max drawdown
    rolling_max = close.cummax()
    drawdown = (close - rolling_max) / rolling_max * 100
    max_drawdown = drawdown.min()

    best_day = daily_ret.max() if daily_ret is not None else None
    worst_day = daily_ret.min() if daily_ret is not None else None

    avg_volume = None
    if volume is not None and volume.sum() > 0:
        avg_volume = volume.mean()

    return {
        "start_date":            str(start_date.date()) if hasattr(start_date, "date") else str(start_date),
        "end_date":              str(end_date.date()) if hasattr(end_date, "date") else str(end_date),
        "total_return_pct":      round(total_return, 4),
        "annualised_return_pct": round(annualised_return, 4) if annualised_return is not None else None,
        "volatility_pct":        round(vol, 4) if vol is not None else None,
        "sharpe_ratio":          round(sharpe, 4) if sharpe is not None else None,
        "max_drawdown_pct":      round(max_drawdown, 4),
        "best_day_pct":          round(best_day, 4) if best_day is not None else None,
        "worst_day_pct":         round(worst_day, 4) if worst_day is not None else None,
        "avg_daily_volume":      round(avg_volume, 2) if avg_volume is not None else None,
    }


def _compute_moving_averages(df: pd.DataFrame) -> pd.DataFrame:
    """Return a DataFrame of close price and 20/50/200-day simple moving averages."""
    close = df["close"] if "close" in df.columns else df["Close"]
    n = len(df)
    result = pd.DataFrame({"close": close}, index=df.index)
    for window in (20, 50, 200):
        col = f"ma_{window}"
        result[col] = close.rolling(window).mean() if n >= window else None
    return result


def _compute_monthly_returns(df: pd.DataFrame) -> pd.DataFrame:
    """Return a pivot table of mean daily returns grouped by year and month."""
    daily_ret = df["daily_return"] if "daily_return" in df.columns else df.get("daily_return")
    tmp = daily_ret.copy().to_frame("daily_return")
    tmp["year"] = df.index.year
    tmp["month"] = df.index.month
    pivot = tmp.groupby(["year", "month"])["daily_return"].mean().unstack("month")
    pivot.columns = [pd.Timestamp(2000, m, 1).strftime("%b") for m in pivot.columns]
    return pivot.round(4)


def _compute_drawdown_series(df: pd.DataFrame) -> pd.Series:
    """Return a Series of rolling drawdown (%) from the running peak close price."""
    close = df["close"] if "close" in df.columns else df["Close"]
    rolling_max = close.cummax()
    return ((close - rolling_max) / rolling_max * 100).rename("drawdown_pct")


def run_analysis(config: dict) -> dict:
    """Run the full analysis for the given config and return a results dict."""
    symbol = config["symbol"]
    logger.info("Starting analysis for %s.", symbol)

    df = _load_prices(config)
    asset_info = _load_info(symbol)

    result = {
        "price_series": df,
        "asset_info":   asset_info,
        "config":       config,
    }

    # summary_stats
    try:
        result["summary_stats"] = _compute_summary_stats(df)
        logger.info("Computed summary stats for %s.", symbol)
    except Exception as exc:
        logger.warning("summary_stats failed for %s: %s", symbol, exc)
        result["summary_stats"] = None

    # moving_averages
    try:
        result["moving_averages"] = _compute_moving_averages(df)
        logger.info("Computed moving averages for %s.", symbol)
    except Exception as exc:
        logger.warning("moving_averages failed for %s: %s", symbol, exc)
        result["moving_averages"] = None

    # monthly_returns
    try:
        if len(df) < 60:
            logger.info("Skipping monthly_returns for %s: fewer than 60 rows.", symbol)
            result["monthly_returns"] = None
        else:
            result["monthly_returns"] = _compute_monthly_returns(df)
            logger.info("Computed monthly returns for %s.", symbol)
    except Exception as exc:
        logger.warning("monthly_returns failed for %s: %s", symbol, exc)
        result["monthly_returns"] = None

    # drawdown_series
    try:
        result["drawdown_series"] = _compute_drawdown_series(df)
        logger.info("Computed drawdown series for %s.", symbol)
    except Exception as exc:
        logger.warning("drawdown_series failed for %s: %s", symbol, exc)
        result["drawdown_series"] = None

    return result


if __name__ == "__main__":
    import explorer
    import fetcher

    config = explorer.interactive_select()
    fetcher.fetch_data(config)
    cleaner.clean_data(config)

    analysis = run_analysis(config)

    stats = analysis["summary_stats"]
    if stats:
        print(f"\n{'='*44}")
        print(f"  Analysis: {config['symbol']} — {config['name']}")
        print(f"{'='*44}")
        for key, val in stats.items():
            label = key.replace("_", " ").title()
            print(f"  {label:<28} {val}")
    else:
        print("Summary stats could not be computed.")
