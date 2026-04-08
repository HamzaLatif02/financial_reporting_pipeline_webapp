"""
PostgreSQL-backed persistence for scheduled jobs.

Uses Render's free PostgreSQL database (DATABASE_URL env var) so jobs
survive service restarts and redeploys — unlike SQLite on Render's
ephemeral filesystem which is wiped on every restart.
"""
from __future__ import annotations

import json
import logging
import os

import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


def _conn():
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not set. Add it to .env for local development "
            "or to Render environment variables for production."
        )
    return psycopg2.connect(url)


def _row_to_dict(row) -> dict:
    return {
        "job_id":        row["job_id"],
        "config":        json.loads(row["config_json"]),
        "schedule":      json.loads(row["schedule_json"]),
        "email":         row["email"],
        "token":         row["token"],
        "confirmed":     row["confirmed"],
        "confirm_token": row.get("confirm_token"),
    }


def init_pg_jobs_table() -> None:
    """Create the scheduled_jobs table and apply schema migrations."""
    with _conn() as conn:
        with conn.cursor() as cur:
            # Create table (idempotent)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS scheduled_jobs (
                    job_id        TEXT PRIMARY KEY,
                    symbol        TEXT NOT NULL,
                    name          TEXT NOT NULL,
                    config_json   TEXT NOT NULL,
                    schedule_json TEXT NOT NULL,
                    email         TEXT NOT NULL,
                    token         TEXT NOT NULL,
                    confirmed     BOOLEAN NOT NULL DEFAULT FALSE,
                    confirm_token TEXT,
                    created_at    TIMESTAMP DEFAULT NOW()
                )
            """)
            # Add new columns safely for existing deployments
            cur.execute("""
                ALTER TABLE scheduled_jobs
                  ADD COLUMN IF NOT EXISTS confirmed BOOLEAN NOT NULL DEFAULT FALSE
            """)
            cur.execute("""
                ALTER TABLE scheduled_jobs
                  ADD COLUMN IF NOT EXISTS confirm_token TEXT
            """)
            # Delete expired unconfirmed jobs (older than 24 hours)
            cur.execute("""
                DELETE FROM scheduled_jobs
                WHERE confirmed = FALSE
                  AND created_at < NOW() - INTERVAL '24 hours'
            """)
            expired = cur.rowcount
        conn.commit()
    if expired:
        logger.info("PG: cleaned up %d expired unconfirmed job(s)", expired)
    logger.info("PG: scheduled_jobs table ready")


def pg_save_job(
    job_id: str,
    config: dict,
    schedule: dict,
    email: str,
    token: str,
    confirmed: bool = False,
    confirm_token: str = None,
) -> None:
    """Insert or update a scheduled job record."""
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO scheduled_jobs
                    (job_id, symbol, name, config_json, schedule_json,
                     email, token, confirmed, confirm_token)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (job_id) DO UPDATE SET
                    config_json   = EXCLUDED.config_json,
                    schedule_json = EXCLUDED.schedule_json,
                    email         = EXCLUDED.email,
                    token         = EXCLUDED.token,
                    confirmed     = EXCLUDED.confirmed,
                    confirm_token = EXCLUDED.confirm_token
            """, (
                job_id,
                config["symbol"],
                config["name"],
                json.dumps(config),
                json.dumps(schedule),
                email,
                token,
                confirmed,
                confirm_token,
            ))
        conn.commit()
    logger.info("PG: saved job %s (confirmed=%s)", job_id, confirmed)


def pg_load_jobs() -> list:
    """Return ALL scheduled jobs (confirmed and pending)."""
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM scheduled_jobs")
            rows = cur.fetchall()
    result = []
    for row in rows:
        try:
            result.append(_row_to_dict(row))
        except Exception as exc:
            logger.error("PG: skipping malformed job %s: %s", row["job_id"], exc)
    logger.info("PG: loaded %d job(s) total", len(result))
    return result


def pg_load_confirmed_jobs() -> list:
    """Return only confirmed (active) scheduled jobs."""
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM scheduled_jobs WHERE confirmed = TRUE")
            rows = cur.fetchall()
    result = []
    for row in rows:
        try:
            result.append(_row_to_dict(row))
        except Exception as exc:
            logger.error("PG: skipping malformed job %s: %s", row["job_id"], exc)
    logger.info("PG: loaded %d confirmed job(s)", len(result))
    return result


def pg_load_pending_jobs() -> list:
    """Return only unconfirmed (pending) scheduled jobs."""
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM scheduled_jobs WHERE confirmed = FALSE")
            rows = cur.fetchall()
    result = []
    for row in rows:
        try:
            result.append(_row_to_dict(row))
        except Exception as exc:
            logger.error("PG: skipping malformed job %s: %s", row["job_id"], exc)
    return result


def confirm_job(confirm_token: str) -> dict | None:
    """Find the job with this confirm_token, mark it confirmed, return its dict.

    Returns None if the token is not found (already used or invalid).
    The confirm_token is cleared after use so the link cannot be replayed.
    """
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM scheduled_jobs WHERE confirm_token = %s AND confirmed = FALSE",
                (confirm_token,),
            )
            row = cur.fetchone()
            if not row:
                return None
            cur.execute(
                """
                UPDATE scheduled_jobs
                   SET confirmed = TRUE, confirm_token = NULL
                 WHERE job_id = %s
                """,
                (row["job_id"],),
            )
        conn.commit()
    logger.info("PG: confirmed job %s", row["job_id"])
    result = _row_to_dict(row)
    result["confirmed"] = True   # reflect the update
    result["confirm_token"] = None
    return result


def pg_get_token_for_job(job_id: str) -> str | None:
    """Return the stored token for any job (confirmed or pending), or None."""
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT token FROM scheduled_jobs WHERE job_id = %s", (job_id,)
            )
            row = cur.fetchone()
    return row[0] if row else None


def pg_get_job(job_id: str) -> dict | None:
    """Return the full job dict for any job, or None."""
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM scheduled_jobs WHERE job_id = %s", (job_id,)
            )
            row = cur.fetchone()
    if not row:
        return None
    try:
        return _row_to_dict(row)
    except Exception as exc:
        logger.error("PG: malformed job %s: %s", job_id, exc)
        return None


def pg_delete_job(job_id: str) -> None:
    """Delete a scheduled job by ID."""
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM scheduled_jobs WHERE job_id = %s", (job_id,))
        conn.commit()
    logger.info("PG: deleted job %s", job_id)
