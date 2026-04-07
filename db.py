import hashlib
import json
import logging
import os
import re
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from config import DB_PATH as _DB_PATH

logging.basicConfig(level=logging.INFO, format="%(levelname)s — %(message)s")
logger = logging.getLogger(__name__)

DB_PATH = Path(_DB_PATH)


def _connect() -> sqlite3.Connection:
    """Open and return a connection to the SQLite database."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def _table_name(symbol: str) -> str:
    """Convert a ticker symbol to a safe SQL table name."""
    safe = re.sub(r"[^a-z0-9]", "_", symbol.lower())
    return f"prices_{safe}"


def _now() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# 1. init_db
# ---------------------------------------------------------------------------

def init_db() -> None:
    """Create data/reporting.db and all required tables."""
    with _connect() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS asset_runs (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol      TEXT    NOT NULL,
                name        TEXT,
                asset_type  TEXT,
                period      TEXT,
                interval    TEXT,
                run_at      TEXT    NOT NULL,
                row_count   INTEGER,
                config_json TEXT
            );

            CREATE TABLE IF NOT EXISTS asset_info (
                symbol      TEXT PRIMARY KEY,
                name        TEXT,
                asset_type  TEXT,
                currency    TEXT,
                info_json   TEXT,
                updated_at  TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS scheduled_jobs (
                job_id        TEXT PRIMARY KEY,
                config_json   TEXT    NOT NULL,
                schedule_json TEXT    NOT NULL,
                email         TEXT    NOT NULL,
                token         TEXT    NOT NULL,
                created_at    TEXT    NOT NULL
            );
        """)
    logger.info("Database initialised at %s", DB_PATH)


# ---------------------------------------------------------------------------
# 2. insert_prices
# ---------------------------------------------------------------------------

def insert_prices(config: dict, df: pd.DataFrame) -> None:
    """Create prices_{symbol} table if needed, insert rows, log to asset_runs."""
    symbol = config["symbol"]
    table = _table_name(symbol)

    create_sql = f"""
        CREATE TABLE IF NOT EXISTS {table} (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            date              TEXT    UNIQUE NOT NULL,
            open              REAL,
            high              REAL,
            low               REAL,
            close             REAL,
            volume            REAL,
            daily_return      REAL,
            cumulative_return REAL,
            typical_price     REAL,
            price_range       REAL,
            vwap              REAL,
            inserted_at       TEXT    NOT NULL
        );
    """

    now = _now()

    # Normalise the Date column to plain date strings (YYYY-MM-DD).
    dates = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")

    rows = [
        (
            dates.iloc[i],
            _float(df, i, "Open"),
            _float(df, i, "High"),
            _float(df, i, "Low"),
            _float(df, i, "Close"),
            _float(df, i, "Volume"),
            _float(df, i, "daily_return"),
            _float(df, i, "cumulative_return"),
            _float(df, i, "typical_price"),
            _float(df, i, "price_range"),
            _float(df, i, "vwap"),
            now,
        )
        for i in range(len(df))
    ]

    insert_sql = f"""
        INSERT OR IGNORE INTO {table}
            (date, open, high, low, close, volume,
             daily_return, cumulative_return, typical_price, price_range, vwap,
             inserted_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    run_sql = """
        INSERT INTO asset_runs
            (symbol, name, asset_type, period, interval, run_at, row_count, config_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """

    with _connect() as conn:
        conn.execute(create_sql)
        conn.executemany(insert_sql, rows)
        conn.execute(run_sql, (
            symbol,
            config.get("name"),
            config.get("asset_type"),
            config.get("period"),
            config.get("interval"),
            now,
            len(df),
            json.dumps(config),
        ))

    logger.info("Inserted %d rows into %s, logged run to asset_runs.", len(df), table)


def _float(df: pd.DataFrame, i: int, col: str):
    """Return float value or None if the column is missing or NaN."""
    if col not in df.columns:
        return None
    val = df[col].iloc[i]
    try:
        return None if pd.isna(val) else float(val)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# 3. insert_info
# ---------------------------------------------------------------------------

def insert_info(config: dict, info: dict) -> None:
    """Upsert asset metadata into asset_info."""
    sql = """
        INSERT OR REPLACE INTO asset_info
            (symbol, name, asset_type, currency, info_json, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """
    with _connect() as conn:
        conn.execute(sql, (
            config["symbol"],
            config.get("name"),
            config.get("asset_type"),
            config.get("currency"),
            json.dumps(info, default=str),
            _now(),
        ))
    logger.info("Upserted asset_info for %s.", config["symbol"])


# ---------------------------------------------------------------------------
# 4. query_prices
# ---------------------------------------------------------------------------

def query_prices(
    symbol: str,
    start_date: str = None,
    end_date: str = None,
) -> pd.DataFrame:
    """Query the prices table for a symbol with optional date range filters.

    Returns a DataFrame with Date as a datetime index.
    """
    table = _table_name(symbol)
    conditions = []
    params = []

    if start_date:
        conditions.append("date >= ?")
        params.append(start_date)
    if end_date:
        conditions.append("date <= ?")
        params.append(end_date)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    sql = f"SELECT * FROM {table} {where} ORDER BY date ASC"

    with _connect() as conn:
        try:
            df = pd.read_sql_query(sql, conn, params=params, parse_dates=["date"])
        except Exception as exc:
            logger.error("Could not query %s: %s", table, exc)
            return pd.DataFrame()

    df.rename(columns={"date": "Date"}, inplace=True)
    df.set_index("Date", inplace=True)
    logger.info("Queried %d rows from %s.", len(df), table)
    return df


# ---------------------------------------------------------------------------
# 5. list_assets
# ---------------------------------------------------------------------------

def list_assets() -> pd.DataFrame:
    """Return all rows from asset_runs, newest first."""
    sql = "SELECT * FROM asset_runs ORDER BY run_at DESC"
    with _connect() as conn:
        df = pd.read_sql_query(sql, conn)
    logger.info("Listed %d asset run(s).", len(df))
    return df


# ---------------------------------------------------------------------------
# 6. scheduled_jobs persistence
# ---------------------------------------------------------------------------

def save_scheduled_job(job_id: str, config: dict, schedule: dict, email: str, token: str) -> None:
    """Insert or replace a scheduled job record."""
    sql = """
        INSERT OR REPLACE INTO scheduled_jobs
            (job_id, config_json, schedule_json, email, token, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """
    with _connect() as conn:
        conn.execute(sql, (
            job_id,
            json.dumps(config),
            json.dumps(schedule),
            email,
            token,
            _now(),
        ))
    logger.info("Saved scheduled job: %s", job_id)


def load_scheduled_jobs() -> list:
    """Return all scheduled jobs as a list of dicts with parsed config/schedule."""
    sql = "SELECT job_id, config_json, schedule_json, email, token FROM scheduled_jobs"
    with _connect() as conn:
        rows = conn.execute(sql).fetchall()
    result = []
    for job_id, config_json, schedule_json, email, token in rows:
        try:
            result.append({
                "job_id":   job_id,
                "config":   json.loads(config_json),
                "schedule": json.loads(schedule_json),
                "email":    email,
                "token":    token,
            })
        except Exception as exc:
            logger.error("Skipping malformed scheduled job %s: %s", job_id, exc)
    logger.info("Loaded %d scheduled job(s) from DB", len(result))
    return result


def delete_scheduled_job(job_id: str) -> bool:
    """Delete a scheduled job; returns True if a row was removed."""
    sql = "DELETE FROM scheduled_jobs WHERE job_id = ?"
    with _connect() as conn:
        cursor = conn.execute(sql, (job_id,))
        deleted = cursor.rowcount > 0
    if deleted:
        logger.info("Deleted scheduled job: %s", job_id)
    return deleted


# ---------------------------------------------------------------------------
# 7. Report cache
# ---------------------------------------------------------------------------

CACHE_TTL = 3600  # 1 hour in seconds


def init_cache_table() -> None:
    """Create the report_cache table if it does not already exist."""
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS report_cache (
                cache_key     TEXT PRIMARY KEY,
                symbol        TEXT NOT NULL,
                name          TEXT NOT NULL,
                asset_type    TEXT NOT NULL,
                currency      TEXT NOT NULL,
                period        TEXT NOT NULL,
                interval_val  TEXT NOT NULL,
                start_date    TEXT,
                end_date      TEXT,
                result_json   TEXT NOT NULL,
                chart_paths   TEXT NOT NULL,
                pdf_path      TEXT NOT NULL,
                created_at    REAL NOT NULL,
                expires_at    REAL NOT NULL
            )
        """)
        conn.commit()
    logger.info("Cache table initialised")


def _make_cache_key(config: dict) -> str:
    """Generate a deterministic SHA-256 cache key from the config fields
    that affect pipeline output: symbol, period, interval, start_date, end_date.
    """
    key_parts = {
        "symbol":     config["symbol"].upper().strip(),
        "period":     config.get("period", "").lower().strip(),
        "interval":   config.get("interval", "").lower().strip(),
        "start_date": config.get("start_date", "") or "",
        "end_date":   config.get("end_date", "") or "",
    }
    key_str = json.dumps(key_parts, sort_keys=True)
    return hashlib.sha256(key_str.encode()).hexdigest()


def get_cached_report(config: dict):
    """Return cached result data if a valid, unexpired entry exists and all
    referenced files are present on disk.  Returns None on any miss.
    """
    cache_key = _make_cache_key(config)
    now = time.time()

    with _connect() as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM report_cache WHERE cache_key = ? AND expires_at > ?",
            (cache_key, now),
        ).fetchone()

    if not row:
        logger.info("Cache miss: %s (no entry or expired)", config["symbol"])
        return None

    chart_paths = json.loads(row["chart_paths"])
    pdf_path = row["pdf_path"]

    missing = [p for p in chart_paths + [pdf_path] if not os.path.exists(p)]
    if missing:
        logger.warning(
            "Cache entry exists for %s but %d file(s) are missing — treating as miss",
            config["symbol"], len(missing),
        )
        delete_cached_report(config)
        return None

    age_minutes = (now - row["created_at"]) / 60
    logger.info("Cache HIT: %s (cached %.1f minutes ago)", config["symbol"], age_minutes)

    return {
        "cache_hit":   True,
        "cached_at":   row["created_at"],
        "expires_at":  row["expires_at"],
        "age_minutes": round(age_minutes, 1),
        "result":      json.loads(row["result_json"]),
        "chart_paths": chart_paths,
        "pdf_path":    pdf_path,
    }


def save_cached_report(
    config: dict,
    result: dict,
    chart_paths: list,
    pdf_path: str,
) -> None:
    """Save pipeline results to the cache.
    Replaces any existing entry for the same cache key.

    `result` should be a JSON-serialisable dict (no DataFrames).
    """
    cache_key = _make_cache_key(config)
    now = time.time()

    with _connect() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO report_cache (
                cache_key, symbol, name, asset_type, currency,
                period, interval_val, start_date, end_date,
                result_json, chart_paths, pdf_path,
                created_at, expires_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cache_key,
            config["symbol"],
            config.get("name", ""),
            config.get("asset_type", ""),
            config.get("currency", ""),
            config.get("period", ""),
            config.get("interval", ""),
            config.get("start_date"),
            config.get("end_date"),
            json.dumps(result, default=str),
            json.dumps(chart_paths),
            pdf_path,
            now,
            now + CACHE_TTL,
        ))
        conn.commit()
    logger.info(
        "Cache saved: %s (expires in %d minutes)",
        config["symbol"], CACHE_TTL // 60,
    )


def delete_cached_report(config: dict) -> None:
    """Delete a specific cache entry by config key."""
    cache_key = _make_cache_key(config)
    with _connect() as conn:
        conn.execute("DELETE FROM report_cache WHERE cache_key = ?", (cache_key,))
        conn.commit()
    logger.info("Cache entry deleted: %s", config["symbol"])


def purge_expired_cache() -> int:
    """Delete all expired cache entries.  Returns the count of deleted rows."""
    now = time.time()
    with _connect() as conn:
        cursor = conn.execute(
            "DELETE FROM report_cache WHERE expires_at <= ?", (now,)
        )
        conn.commit()
        deleted = cursor.rowcount
    if deleted > 0:
        logger.info("Cache purged: %d expired entries removed", deleted)
    return deleted


def list_cache_entries() -> list:
    """Return all active (non-expired) cache entries, newest first."""
    now = time.time()
    with _connect() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """SELECT symbol, name, period, interval_val,
                      created_at, expires_at
               FROM report_cache
               WHERE expires_at > ?
               ORDER BY created_at DESC""",
            (now,),
        ).fetchall()
    return [dict(row) for row in rows]


# ---------------------------------------------------------------------------
# Main guard
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    init_db()
    print(f"Database ready at {DB_PATH}")
