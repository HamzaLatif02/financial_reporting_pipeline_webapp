import json
import logging
import smtplib
import sys
import traceback
from datetime import date
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import os

from dotenv import load_dotenv

import analysis as ana
import charts as ch
import cleaner
import db
import explorer
import fetcher
import report as rpt

# ── Logging ───────────────────────────────────────────────────────────────────

Path("data").mkdir(exist_ok=True)

_fmt = "%(asctime)s — %(levelname)s — %(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=_fmt,
    force=True,   # override any handlers added by imported modules
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("data/pipeline.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────────

CONFIG_DIR = Path("data")


def _config_path(symbol: str) -> Path:
    """Return the path to the saved config JSON for a symbol."""
    return CONFIG_DIR / f"{symbol}_config.json"


def _save_config(config: dict) -> None:
    """Persist the pipeline config dict to data/{symbol}_config.json."""
    path = _config_path(config["symbol"])
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(config, f, indent=2)
    logger.info("Config saved to %s", path)


# ── Email ─────────────────────────────────────────────────────────────────────

def _smtp_settings() -> dict:
    """Load and return SMTP connection settings from environment variables."""
    load_dotenv()
    return {
        "host":      os.getenv("SMTP_HOST", "smtp.gmail.com"),
        "port":      int(os.getenv("SMTP_PORT", 587)),
        "user":      os.getenv("SMTP_USER", ""),
        "password":  os.getenv("SMTP_PASSWORD", ""),
        "recipient": os.getenv("REPORT_RECIPIENT", ""),
    }


def _credentials_configured(smtp: dict) -> bool:
    """Return True only if all SMTP fields are set and not placeholder values."""
    placeholders = {"", "your_email@gmail.com", "your_app_password"}
    for field in ("user", "password", "recipient"):
        val = smtp.get(field, "")
        if not val or val in placeholders or val.startswith("your_"):
            return False
    return True


def _send_email(subject: str, body: str, attachment_path: str = None) -> None:
    """Send an email with an optional PDF attachment via SMTP/TLS."""
    smtp = _smtp_settings()
    if not _credentials_configured(smtp):
        logger.warning(
            "SMTP credentials are placeholder or unset — skipping email. "
            "Fill in SMTP_USER, SMTP_PASSWORD and REPORT_RECIPIENT in .env "
            "to enable delivery."
        )
        return

    msg = MIMEMultipart()
    msg["From"]    = smtp["user"]
    msg["To"]      = smtp["recipient"]
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    if attachment_path and Path(attachment_path).exists():
        with open(attachment_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename={Path(attachment_path).name}",
        )
        msg.attach(part)

    with smtplib.SMTP(smtp["host"], smtp["port"]) as server:
        server.ehlo()
        server.starttls()
        server.login(smtp["user"], smtp["password"])
        server.sendmail(smtp["user"], smtp["recipient"], msg.as_string())

    logger.info("Email sent to %s: %s", smtp["recipient"], subject)


def _build_stats_body(config: dict, analysis: dict) -> str:
    """Format summary_stats as a plain-text email body."""
    stats = analysis.get("summary_stats") or {}
    lines = [
        f"Financial Report — {config['name']} ({config['symbol']})",
        f"Generated: {date.today().isoformat()}",
        "",
        "Summary Statistics",
        "=" * 36,
    ]
    labels = {
        "start_date":            "Start Date",
        "end_date":              "End Date",
        "total_return_pct":      "Total Return",
        "annualised_return_pct": "Annualised Return",
        "volatility_pct":        "Volatility (ann.)",
        "sharpe_ratio":          "Sharpe Ratio",
        "max_drawdown_pct":      "Max Drawdown",
        "best_day_pct":          "Best Day",
        "worst_day_pct":         "Worst Day",
        "avg_daily_volume":      "Avg Daily Volume",
    }
    pct_keys = {
        "total_return_pct", "annualised_return_pct", "volatility_pct",
        "max_drawdown_pct", "best_day_pct", "worst_day_pct",
    }
    for key, label in labels.items():
        val = stats.get(key)
        if val is None:
            fmt = "N/A"
        elif key in pct_keys:
            fmt = f"{val:+.2f}%"
        elif key == "sharpe_ratio":
            fmt = f"{val:.2f}"
        elif key == "avg_daily_volume":
            fmt = f"{val:,.0f}"
        else:
            fmt = str(val)
        lines.append(f"  {label:<28} {fmt}")

    lines += ["", "Source: Yahoo Finance via yfinance",
              "This report is for educational purposes only."]
    return "\n".join(lines)


def _send_failure_alert(stage: str, symbol: str, tb: str) -> None:
    """Send a plain-text failure alert email with the traceback."""
    subject = f"Pipeline FAILED — {symbol} at stage: {stage}"
    body = f"The pipeline failed at stage '{stage}' for {symbol}.\n\n{tb}"
    try:
        _send_email(subject, body)
    except Exception as exc:
        logger.error("Could not send failure alert: %s", exc)


# ── Pipeline stages ───────────────────────────────────────────────────────────

def _run_stage(name: str, fn, symbol: str, *args, **kwargs):
    """Run a pipeline stage, re-raising on failure after logging."""
    logger.info("Stage [%s] starting.", name)
    try:
        result = fn(*args, **kwargs)
        logger.info("Stage [%s] complete.", name)
        return result
    except Exception:
        tb = traceback.format_exc()
        logger.error("Stage [%s] FAILED:\n%s", name, tb)
        _send_failure_alert(name, symbol, tb)
        sys.exit(1)


# ── Public API ────────────────────────────────────────────────────────────────

def run_pipeline(config: dict = None) -> None:
    """Run the full pipeline.

    If config is None, launches interactive asset selection (Mode A).
    If config is provided, runs in replay mode (Mode B).
    """
    load_dotenv()

    # ── 1. Config ─────────────────────────────────────────────────────────────
    if config is None:
        logger.info("Mode A: interactive asset selection.")
        config = _run_stage("explorer", explorer.interactive_select, "unknown")
        _save_config(config)
    else:
        logger.info("Mode B: replay config for %s.", config.get("symbol", "?"))

    symbol = config["symbol"]
    logger.info("Pipeline started for %s.", symbol)

    # ── 2. Fetch ──────────────────────────────────────────────────────────────
    raw = _run_stage("fetch", fetcher.fetch_data, symbol, config)

    # ── 3. Clean ──────────────────────────────────────────────────────────────
    df = _run_stage("clean", cleaner.clean_data, symbol, config)

    # ── 4. Insert prices ──────────────────────────────────────────────────────
    _run_stage("db.insert_prices", db.insert_prices, symbol, config, df)

    # ── 5. Insert info ────────────────────────────────────────────────────────
    info = raw.get("info", {})
    _run_stage("db.insert_info", db.insert_info, symbol, config, info)

    # ── 6. Analysis ───────────────────────────────────────────────────────────
    analysis = _run_stage("analysis", ana.run_analysis, symbol, config)

    # ── 7. Charts ─────────────────────────────────────────────────────────────
    chart_paths = _run_stage("charts", ch.generate_charts, symbol, config, analysis)

    # ── 8. Report ─────────────────────────────────────────────────────────────
    pdf_path = _run_stage("report", rpt.generate_report, symbol,
                          config, analysis, chart_paths)

    # ── 9. Email ──────────────────────────────────────────────────────────────
    name = config["name"]
    subject = f"{name} ({symbol}) Report — {date.today().isoformat()}"
    body = _build_stats_body(config, analysis)

    logger.info("Stage [email] starting.")
    try:
        _send_email(subject, body, pdf_path)
        logger.info("Stage [email] complete.")
    except Exception:
        # Email failure is non-fatal — the PDF is already saved.
        logger.warning("Stage [email] failed (non-fatal):\n%s", traceback.format_exc())

    logger.info("Pipeline complete for %s. Report: %s", symbol, pdf_path)
    print(f"\nDone. Report saved to: {pdf_path}")


# ── Main guard ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    run_pipeline()
