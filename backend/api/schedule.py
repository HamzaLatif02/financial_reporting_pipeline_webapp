import logging
import os
import re
import sys

from flask import Blueprint, jsonify, request

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from scheduler import add_job, remove_job, list_jobs  # noqa: E402

schedule_bp = Blueprint("schedule", __name__)
logger = logging.getLogger(__name__)

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

_REQUIRED_CONFIG = {"symbol", "name", "asset_type", "currency", "period", "interval"}
_VALID_FREQUENCIES = {"daily", "weekly", "monthly"}


def _validate_email(addr: str) -> bool:
    return bool(_EMAIL_RE.match(addr or ""))


@schedule_bp.post("/add")
def add():
    body = request.get_json(silent=True) or {}

    email     = (body.get("email") or "").strip()
    frequency = (body.get("frequency") or "").strip()
    config    = body.get("config") or {}

    # ── Validate
    errors = []
    if not _validate_email(email):
        errors.append("Valid email address is required.")
    if frequency not in _VALID_FREQUENCIES:
        errors.append(f"frequency must be one of: {', '.join(_VALID_FREQUENCIES)}.")
    missing_cfg = _REQUIRED_CONFIG - config.keys()
    if missing_cfg:
        errors.append(f"config is missing fields: {', '.join(sorted(missing_cfg))}.")
    if frequency == "weekly" and not body.get("day_of_week"):
        errors.append("day_of_week is required for weekly frequency.")
    if frequency == "monthly" and not body.get("day"):
        errors.append("day is required for monthly frequency.")
    if errors:
        return jsonify({"error": " ".join(errors)}), 400

    schedule = {
        "frequency":   frequency,
        "hour":        int(body.get("hour", 8)),
        "minute":      int(body.get("minute", 0)),
        "day_of_week": body.get("day_of_week"),
        "day":         body.get("day"),
    }

    # Sanitise email for use in job_id
    safe_email = re.sub(r"[^a-zA-Z0-9]", "_", email)
    job_id     = f"{config['symbol']}_{safe_email}_{frequency}"

    try:
        add_job(job_id, config, schedule, email)
    except Exception as exc:
        logger.exception("add_job failed")
        return jsonify({"error": str(exc)}), 500

    # Retrieve next_run_time from the live job list
    jobs = list_jobs()
    job  = next((j for j in jobs if j["job_id"] == job_id), None)
    next_run = job["next_run_time"] if job else None

    return jsonify({"status": "scheduled", "job_id": job_id, "next_run": next_run})


@schedule_bp.delete("/remove/<job_id>")
def remove(job_id: str):
    try:
        existed = remove_job(job_id)
    except Exception as exc:
        logger.exception("remove_job failed")
        return jsonify({"error": str(exc)}), 500

    if not existed:
        return jsonify({"error": f"Job '{job_id}' not found."}), 404

    return jsonify({"status": "removed", "job_id": job_id})


@schedule_bp.get("/list")
def list_all():
    try:
        jobs = list_jobs()
        return jsonify({"jobs": jobs})
    except Exception as exc:
        logger.exception("list_jobs failed")
        return jsonify({"error": str(exc)}), 500
