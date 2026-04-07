import json
import logging
from pathlib import Path

import pandas as pd
import yfinance as yf

from config import RAW_DIR as _RAW_DIR

logging.basicConfig(level=logging.INFO, format="%(levelname)s — %(message)s")
logger = logging.getLogger(__name__)

RAW_DIR = Path(_RAW_DIR)


def fetch_data(config: dict) -> dict:
    """Fetch OHLCV price history and asset metadata for the given config.

    Saves raw outputs to data/raw/ and returns:
        {"prices": pd.DataFrame, "info": dict}
    """
    from datetime import date as _date, datetime as _datetime

    symbol   = config["symbol"]
    interval = config["interval"]
    ticker   = yf.Ticker(symbol)

    # --- Price history ---
    if config.get("period") == "custom":
        start = config.get("start_date")
        end   = config.get("end_date")

        if not start or not end:
            raise ValueError(
                "start_date and end_date are required when period is 'custom'"
            )
        today = _date.today().isoformat()
        if end > today:
            raise ValueError("End date cannot be in the future")
        if start >= end:
            raise ValueError("start_date must be before end_date")

        delta_days = (_datetime.fromisoformat(end) - _datetime.fromisoformat(start)).days
        if delta_days < 7:
            raise ValueError("Date range must be at least 7 days")

        if interval == "1wk" and delta_days < 28:
            logger.warning(
                "Weekly interval with less than 4 weeks of data for %s", symbol
            )
        if interval == "1mo" and delta_days < 90:
            logger.warning(
                "Monthly interval with less than 3 months of data for %s", symbol
            )

        logger.info("Fetching %s: %s to %s (%s)", symbol, start, end, interval)
        df = ticker.history(start=start, end=end, interval=interval)
    else:
        logger.info(
            "Fetching %s: period=%s (%s)", symbol, config["period"], interval
        )
        df = ticker.history(period=config["period"], interval=interval)

    df.reset_index(inplace=True)

    # Normalise the date column name — yfinance uses "Date" for daily/weekly
    # and "Datetime" for intraday intervals.
    if "Datetime" in df.columns:
        df.rename(columns={"Datetime": "Date"}, inplace=True)

    # Keep only the standard OHLCV columns (plus Date).
    ohlcv_cols = ["Date", "Open", "High", "Low", "Close", "Volume"]
    df = df[[c for c in ohlcv_cols if c in df.columns]]

    # --- Asset metadata ---
    try:
        info_dict = ticker.info or {}
    except Exception as exc:
        logger.warning("Could not fetch info for %s: %s", symbol, exc)
        info_dict = {}

    # --- Persist to disk ---
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    prices_path = RAW_DIR / f"{symbol}_prices.csv"
    info_path = RAW_DIR / f"{symbol}_info.json"

    df.to_csv(prices_path, index=False)

    with open(info_path, "w") as f:
        json.dump(info_dict, f, indent=2, default=str)

    # --- Logging ---
    if not df.empty:
        date_from = df["Date"].iloc[0]
        date_to = df["Date"].iloc[-1]
        logger.info(
            "Fetched %s: %d rows from %s to %s",
            symbol, len(df), date_from, date_to,
        )
    else:
        logger.warning("Fetched %s: no price data returned.", symbol)

    return {"prices": df, "info": info_dict}


def load_raw(symbol: str) -> dict:
    """Load previously saved raw data for a symbol from data/raw/.

    Returns:
        {"prices": pd.DataFrame, "info": dict}
    """
    prices_path = RAW_DIR / f"{symbol}_prices.csv"
    info_path = RAW_DIR / f"{symbol}_info.json"

    if not prices_path.exists():
        raise FileNotFoundError(f"No saved price data for '{symbol}': {prices_path}")
    if not info_path.exists():
        raise FileNotFoundError(f"No saved info data for '{symbol}': {info_path}")

    df = pd.read_csv(prices_path, parse_dates=["Date"])

    with open(info_path) as f:
        info_dict = json.load(f)

    logger.info("Loaded raw data for %s: %d rows", symbol, len(df))
    return {"prices": df, "info": info_dict}


if __name__ == "__main__":
    import explorer
    config = explorer.interactive_select()
    result = fetch_data(config)

    df = result["prices"]
    if not df.empty:
        print(f"\nSymbol:     {config['symbol']}")
        print(f"Date range: {df['Date'].iloc[0]} → {df['Date'].iloc[-1]}")
        print(f"Rows:       {len(df)}")
    else:
        print(f"\nSymbol: {config['symbol']} — no data returned.")
