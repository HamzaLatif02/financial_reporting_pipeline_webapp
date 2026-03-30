# Financial Reporting Pipeline

An automated Python pipeline that fetches financial data, generates reports, and delivers them via email on a schedule.

## Overview

<!-- Describe what this pipeline does, what data sources it uses, and what outputs it produces. -->

## Project Structure

```
financial-pipeline/
├── data/
│   ├── raw/        # Raw data fetched from sources
│   ├── clean/      # Processed and cleaned data
│   └── charts/     # Generated chart images
├── tests/          # Unit and integration tests
├── .env            # Environment variables (not tracked)
├── .gitignore
├── requirements.txt
└── README.md
```

## Setup

<!-- Step-by-step instructions for setting up the project locally. -->

1. Clone the repository
2. Create and activate a virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Copy `.env` and fill in your credentials

## How to Run

<!-- Instructions for running the pipeline manually or on a schedule. -->

## Tech Stack

| Library | Purpose |
|---|---|
| yfinance | Fetching financial market data |
| pandas / numpy | Data processing and analysis |
| matplotlib / seaborn / mplfinance | Charting and visualization |
| fpdf2 | PDF report generation |
| openpyxl | Excel report generation |
| python-dotenv | Environment variable management |
| APScheduler | Scheduling automated runs |
| pytest | Testing |
| tabulate | Table formatting |
