# Financial Reporting Pipeline

An automated Python pipeline that fetches price data for any asset on Yahoo Finance, runs quantitative analysis, generates a multi-page PDF report with charts, and delivers it by email on a weekday schedule — with no API key required.

The pipeline supports all five major asset classes available through Yahoo Finance: stocks, ETFs and indices, forex pairs, cryptocurrencies, and commodities. Assets are selected interactively by ticker symbol. Once a configuration is saved, the scheduler replays the full pipeline unattended every weekday morning.

---

## How It Works

**Step 1 — Run once interactively**

```bash
python pipeline.py
```

You will be guided through an asset selection menu. Choose a category, pick a ticker or enter your own, then select a period and interval. The pipeline runs all stages automatically:

```
fetch → clean → store → analyse → chart → PDF report → email
```

Your configuration is saved to `data/{symbol}_config.json`.

**Step 2 — Schedule for automatic daily delivery**

```bash
python scheduler.py
```

The scheduler scans `data/` for all saved `*_config.json` files and runs each pipeline every weekday (Mon–Fri) at 07:30. No further interaction required.

---

## Example Assets

| Ticker | Name | Category | Why interesting |
|---|---|---|---|
| `AAPL` | Apple Inc. | Stock | Mega-cap benchmark, high liquidity |
| `TSLA` | Tesla Inc. | Stock | High volatility, retail-driven momentum |
| `SPY` | SPDR S&P 500 ETF | ETF | Broadest US market proxy |
| `^FTSE` | FTSE 100 Index | Index | UK large-cap benchmark |
| `VWRL.L` | Vanguard All-World ETF | ETF | Global diversification in one ticker |
| `GBPUSD=X` | British Pound / US Dollar | Forex | Key macro pair, sensitive to UK events |
| `BTC-USD` | Bitcoin | Crypto | Dominant digital asset, extreme volatility |
| `GC=F` | Gold Futures | Commodity | Safe-haven asset, inflation proxy |
| `CL=F` | Crude Oil Futures | Commodity | Energy market bellwether |
| `^TNX` | US 10-Year Treasury Yield | Macro | Risk-free rate benchmark |

---

## Architecture

| Module | Role |
|---|---|
| `explorer.py` | Interactive CLI for selecting any Yahoo Finance asset. Validates tickers live via `yfinance`, presents categorised menus, and returns a config dict. |
| `fetcher.py` | Fetches OHLCV price history and asset metadata using `yf.Ticker`. Saves raw CSV and JSON to `data/raw/`. |
| `cleaner.py` | Loads raw prices, removes nulls and duplicates, sorts by date, and computes derived columns: `daily_return`, `cumulative_return`, `typical_price`, `price_range`, and `vwap`. Saves to `data/clean/`. |
| `db.py` | SQLite persistence layer. Maintains three tables: `prices_{symbol}` (OHLCV + derived), `asset_runs` (pipeline audit log), and `asset_info` (latest metadata per asset). |
| `analysis.py` | Loads prices from the DB (falls back to CSV), computes summary statistics, moving averages, monthly return pivot, and drawdown series. Returns a structured results dict. |
| `charts.py` | Generates six PNG charts using matplotlib, seaborn, and mplfinance: candlestick, price + MAs, cumulative return, drawdown, monthly returns heatmap, and a summary statistics table. |
| `report.py` | Builds a multi-page PDF using fpdf2. Sections: title page, key metrics, asset info, six chart pages, and a disclaimer. |
| `pipeline.py` | Orchestrator. Runs all stages in order, wraps each in structured error handling, logs to console and file, emails the PDF on completion. Supports interactive (Mode A) and replay (Mode B) operation. |
| `scheduler.py` | APScheduler wrapper. Discovers all saved configs and schedules a pipeline run per asset, Mon–Fri at 07:30, with a heartbeat log every 5 minutes. |

---

## Tech Stack

| Library | Purpose |
|---|---|
| `yfinance` | Fetches price history and asset metadata from Yahoo Finance with no API key |
| `pandas` | Core data structure for all price and analysis DataFrames |
| `numpy` | Numerical operations (standard deviation, square root for annualisation) |
| `matplotlib` | Base charting library for all custom plots |
| `seaborn` | Monthly returns heatmap and `whitegrid` theme |
| `mplfinance` | Purpose-built candlestick chart with volume bars |
| `fpdf2` | PDF generation with fine-grained layout control |
| `openpyxl` | Excel compatibility layer (pandas dependency) |
| `python-dotenv` | Loads SMTP credentials from `.env` without hardcoding secrets |
| `APScheduler` | Background job scheduler with cron trigger support |
| `tabulate` | Table formatting utility |
| `pytest` | Unit test framework |

---

## Metrics Explained

| Metric | Definition |
|---|---|
| **Total Return** | Percentage gain or loss from the first to the last closing price in the period: `(last − first) / first × 100` |
| **Annualised Return** | Compound annual growth rate over the period: `(1 + total_return) ^ (1 / years) − 1` |
| **Volatility** | Annualised standard deviation of daily returns: `std(daily_returns) × √252` — measures the magnitude of price swings |
| **Sharpe Ratio** | Risk-adjusted return: `annualised_return / volatility` (assuming 0% risk-free rate) — higher is better |
| **Max Drawdown** | Largest peak-to-trough decline in closing price during the period — measures worst-case loss from a high |
| **Best Day** | Highest single-day percentage return in the period |
| **Worst Day** | Lowest single-day percentage return in the period |

---

## Setup

**Requirements:** Python 3.9+

```bash
# 1. Clone the repository
git clone https://github.com/HamzaLatif02/financial_reporting_pipeline.git
cd financial_reporting_pipeline

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure email delivery (optional)
cp .env .env.local               # edit with your SMTP credentials
```

**.env file:**

```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password   # use a Gmail App Password, not your login password
REPORT_RECIPIENT=recipient@example.com
```

Email delivery is optional. If credentials are not set, the pipeline completes and saves the PDF locally without sending anything.

---

## How to Run

**Interactive — select an asset and generate a report:**

```bash
python pipeline.py
```

Follow the on-screen prompts to select an asset category, ticker, period, and interval. The full pipeline runs automatically and saves a PDF to `data/{symbol}_report.pdf`.

**Scheduled — repeat daily for all saved assets:**

```bash
python scheduler.py
```

Runs every weekday at 07:30 for each asset that has a saved `data/*_config.json`. Stop with `Ctrl+C`.

**Tests:**

```bash
pytest tests/
```

---

## Project Structure

```
financial_reporting_pipeline/
├── explorer.py          # Interactive asset selection
├── fetcher.py           # Yahoo Finance data fetching
├── cleaner.py           # Data cleaning and derived metrics
├── db.py                # SQLite storage layer
├── analysis.py          # Quantitative analysis
├── charts.py            # Chart generation (6 chart types)
├── report.py            # PDF report generation
├── pipeline.py          # Pipeline orchestrator
├── scheduler.py         # Weekday scheduler
│
├── tests/
│   └── test_cleaner.py  # Unit tests for the cleaning module
│
├── data/
│   ├── raw/             # Raw CSV and JSON from yfinance (gitignored)
│   ├── clean/           # Cleaned price CSVs (gitignored)
│   ├── charts/          # Generated chart PNGs (gitignored)
│   ├── reporting.db     # SQLite database (gitignored)
│   ├── pipeline.log     # Pipeline run log (gitignored)
│   └── {symbol}_config.json  # Saved asset configurations
│
├── .env                 # SMTP credentials (gitignored)
├── requirements.txt
└── README.md
```

---

## Disclaimer

This project fetches data from Yahoo Finance via the `yfinance` library for educational and portfolio tracking purposes only. Data accuracy is not guaranteed. Nothing in this project constitutes financial advice. Always verify data independently before making any investment decision.
