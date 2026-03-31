import logging
from typing import Optional
import yfinance as yf

logging.basicConfig(level=logging.INFO, format="%(levelname)s — %(message)s")
logger = logging.getLogger(__name__)

ASSET_CATEGORIES = {
    "Stocks": {
        "description": "Individual company shares",
        "examples": [
            ("AAPL",   "Apple Inc."),
            ("MSFT",   "Microsoft Corp."),
            ("GOOGL",  "Alphabet Inc."),
            ("AMZN",   "Amazon.com Inc."),
            ("TSLA",   "Tesla Inc."),
            ("LLOY.L", "Lloyds Banking Group (LSE)"),
            ("SHEL.L", "Shell Plc (LSE)"),
            ("BP.L",   "BP Plc (LSE)"),
        ]
    },
    "ETFs & Indices": {
        "description": "Funds and market indices",
        "examples": [
            ("SPY",    "SPDR S&P 500 ETF"),
            ("QQQ",    "Invesco Nasdaq-100 ETF"),
            ("VWRL.L", "Vanguard FTSE All-World ETF (LSE)"),
            ("^GSPC",  "S&P 500 Index"),
            ("^FTSE",  "FTSE 100 Index"),
            ("^DJI",   "Dow Jones Industrial Average"),
            ("^IXIC",  "Nasdaq Composite"),
        ]
    },
    "Forex": {
        "description": "Currency exchange rates",
        "examples": [
            ("GBPUSD=X", "British Pound / US Dollar"),
            ("EURUSD=X", "Euro / US Dollar"),
            ("USDJPY=X", "US Dollar / Japanese Yen"),
            ("GBPEUR=X", "British Pound / Euro"),
            ("EURGBP=X", "Euro / British Pound"),
        ]
    },
    "Cryptocurrency": {
        "description": "Digital asset prices in USD",
        "examples": [
            ("BTC-USD", "Bitcoin"),
            ("ETH-USD", "Ethereum"),
            ("SOL-USD", "Solana"),
            ("BNB-USD", "Binance Coin"),
            ("XRP-USD", "XRP"),
        ]
    },
    "Commodities & Macro": {
        "description": "Gold, oil, bonds and economic proxies",
        "examples": [
            ("GC=F",  "Gold Futures (USD/oz)"),
            ("CL=F",  "Crude Oil Futures (USD/bbl)"),
            ("^TNX",  "US 10-Year Treasury Yield"),
            ("^TYX",  "US 30-Year Treasury Yield"),
            ("^IRX",  "US 13-Week T-Bill Rate"),
        ]
    }
}

PERIODS = [
    ("1mo",  "1 month"),
    ("3mo",  "3 months"),
    ("6mo",  "6 months"),
    ("1y",   "1 year"),
    ("2y",   "2 years"),
    ("5y",   "5 years"),
    ("10y",  "10 years"),
    ("max",  "Maximum available history"),
]

INTERVALS = [
    ("1d",  "Daily"),
    ("1wk", "Weekly"),
    ("1mo", "Monthly"),
]

# Minimum recommended period for each interval to avoid sparse data
_MIN_PERIOD_INDEX = {
    "1wk": 1,   # at least 3mo
    "1mo": 3,   # at least 6mo
}


def validate_ticker(symbol: str) -> Optional[dict]:
    """Fetch metadata for a ticker symbol from Yahoo Finance.

    Returns a dict with symbol, name, type, currency, exchange,
    or None if the ticker cannot be found.
    """
    try:
        info = yf.Ticker(symbol).info
    except Exception as exc:
        logger.warning("Error fetching ticker %s: %s", symbol, exc)
        return None

    if not info or info.get("trailingPegRatio") is None and len(info) <= 1:
        logger.warning("Ticker not found or empty info: %s", symbol)
        return None

    result = {
        "symbol":   info.get("symbol", symbol).upper(),
        "name":     info.get("longName") or info.get("shortName") or symbol,
        "type":     info.get("quoteType", "Unknown"),
        "currency": info.get("currency", "N/A"),
        "exchange": info.get("exchange", "N/A"),
    }
    logger.info("Validated ticker: %s (%s) on %s", result["symbol"], result["name"], result["exchange"])
    return result


def _prompt_int(prompt: str, lo: int, hi: int) -> int:
    """Prompt until the user enters an integer in [lo, hi]."""
    while True:
        raw = input(prompt).strip()
        if raw.isdigit() and lo <= int(raw) <= hi:
            return int(raw)
        print(f"  Please enter a number between {lo} and {hi}.")


def _select_asset() -> tuple[str, str, str]:
    """Walk the user through category → asset selection.

    Returns (symbol, name, asset_type).
    """
    category_names = list(ASSET_CATEGORIES.keys())

    while True:
        print("\nAsset categories:")
        for i, name in enumerate(category_names, 1):
            desc = ASSET_CATEGORIES[name]["description"]
            print(f"  {i}. {name} — {desc}")

        choice = _prompt_int(
            "Select a category or type 0 to enter a custom ticker: ",
            lo=0, hi=len(category_names)
        )

        if choice == 0:
            symbol, name = _prompt_custom_ticker()
            return symbol, name, "Custom"

        category = category_names[choice - 1]
        examples = ASSET_CATEGORIES[category]["examples"]

        print(f"\n{category} — example tickers:")
        for i, (ticker, label) in enumerate(examples, 1):
            print(f"  {i}. {ticker:12s} {label}")

        asset_choice = _prompt_int(
            "Select an asset or type 0 to enter a custom ticker: ",
            lo=0, hi=len(examples)
        )

        if asset_choice == 0:
            symbol, name = _prompt_custom_ticker()
            return symbol, name, category

        ticker, label = examples[asset_choice - 1]
        return ticker, label, category


def _prompt_custom_ticker() -> tuple[str, str]:
    """Prompt for a custom ticker symbol, validating against Yahoo Finance.

    Loops until a valid ticker is entered. Returns (symbol, name).
    """
    while True:
        symbol = input("Enter ticker symbol (e.g. AAPL, BTC-USD): ").strip().upper()
        if not symbol:
            print("  Symbol cannot be empty.")
            continue
        print(f"  Validating {symbol}...")
        info = validate_ticker(symbol)
        if info:
            return info["symbol"], info["name"]
        print(f"  Could not find '{symbol}' on Yahoo Finance. Please try again.")


def _select_period() -> str:
    """Print the PERIODS list and return the chosen period code."""
    print("\nAvailable periods:")
    for i, (code, label) in enumerate(PERIODS, 1):
        print(f"  {i}. {label} ({code})")
    choice = _prompt_int("Select a period: ", lo=1, hi=len(PERIODS))
    return PERIODS[choice - 1][0]


def _select_interval() -> str:
    """Print the INTERVALS list and return the chosen interval code."""
    print("\nAvailable intervals:")
    for i, (code, label) in enumerate(INTERVALS, 1):
        print(f"  {i}. {label} ({code})")
    choice = _prompt_int("Select an interval: ", lo=1, hi=len(INTERVALS))
    return INTERVALS[choice - 1][0]


def _check_period_interval(period: str, interval: str) -> None:
    """Warn if the period is too short for the chosen interval."""
    period_index = next(i for i, (p, _) in enumerate(PERIODS) if p == period)
    min_index = _MIN_PERIOD_INDEX.get(interval)
    if min_index is not None and period_index < min_index:
        min_label = PERIODS[min_index][1]
        interval_label = next(l for c, l in INTERVALS if c == interval)
        print(
            f"  Warning: {interval_label} interval with a very short period may "
            f"produce very few data points. Consider {min_label} or longer."
        )


def interactive_select() -> dict:
    """Interactively guide the user to select an asset and configure a data pull.

    Returns a config dict with keys:
        symbol, name, asset_type, currency, period, interval
    """
    print("=" * 50)
    print("  Financial Asset Explorer")
    print("=" * 50)

    symbol, name, asset_type = _select_asset()

    period = _select_period()
    interval = _select_interval()

    _check_period_interval(period, interval)

    # Fetch currency for the chosen ticker (best-effort)
    info = validate_ticker(symbol)
    currency = info["currency"] if info else "N/A"

    config = {
        "symbol":     symbol,
        "name":       name,
        "asset_type": asset_type,
        "currency":   currency,
        "period":     period,
        "interval":   interval,
    }

    return config


if __name__ == "__main__":
    config = interactive_select()
    print("\nSelected configuration:")
    for key, value in config.items():
        print(f"  {key}: {value}")
