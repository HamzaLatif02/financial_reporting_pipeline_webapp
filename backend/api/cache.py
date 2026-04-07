import logging
import os
import sys
import time

from flask import Blueprint, jsonify, request

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from db import (  # noqa: E402
    list_cache_entries, purge_expired_cache,
    delete_cached_report, _make_cache_key,
)
from extensions import limiter  # noqa: E402

cache_bp = Blueprint("cache", __name__)
logger = logging.getLogger(__name__)

_ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")


def _check_admin() -> bool:
    """Return True if the X-Admin-Token header matches ADMIN_TOKEN env var."""
    if not _ADMIN_TOKEN:
        return True  # no token configured — open in dev
    return request.headers.get("X-Admin-Token", "") == _ADMIN_TOKEN


# ── GET /api/cache/status ─────────────────────────────────────────────────────

@cache_bp.get("/status")
@limiter.exempt
def status():
    """Return all active cache entries with time-until-expiry."""
    now = time.time()
    entries = list_cache_entries()
    result = []
    for e in entries:
        secs_left = max(0, e["expires_at"] - now)
        mins_left = int(secs_left // 60)
        result.append({
            "symbol":      e["symbol"],
            "name":        e["name"],
            "period":      e["period"],
            "interval":    e["interval_val"],
            "cached_at":   e["created_at"],
            "expires_at":  e["expires_at"],
            "expires_in":  f"{mins_left} minute{'s' if mins_left != 1 else ''}",
        })
    return jsonify({"entries": result, "count": len(result)})


# ── DELETE /api/cache/purge ───────────────────────────────────────────────────

@cache_bp.delete("/purge")
def purge():
    """Delete all expired cache entries.  Requires X-Admin-Token."""
    if not _check_admin():
        return jsonify({"error": "Unauthorized"}), 403

    deleted = purge_expired_cache()
    return jsonify({
        "deleted": deleted,
        "message": f"{deleted} expired {'entry' if deleted == 1 else 'entries'} removed",
    })


# ── DELETE /api/cache/invalidate ──────────────────────────────────────────────

@cache_bp.delete("/invalidate")
def invalidate():
    """Delete a specific cache entry by symbol/period/interval.
    Body: {"symbol": "AAPL", "period": "1y", "interval": "1d"}
    Requires X-Admin-Token.
    """
    if not _check_admin():
        return jsonify({"error": "Unauthorized"}), 403

    body = request.get_json(silent=True) or {}
    symbol = (body.get("symbol") or "").strip().upper()
    if not symbol:
        return jsonify({"error": "symbol is required"}), 400

    config = {
        "symbol":     symbol,
        "period":     (body.get("period") or "").lower().strip(),
        "interval":   (body.get("interval") or "").lower().strip(),
        "start_date": body.get("start_date") or "",
        "end_date":   body.get("end_date") or "",
    }

    try:
        delete_cached_report(config)
    except Exception as exc:
        logger.exception("Cache invalidate failed")
        return jsonify({"error": str(exc)}), 500

    return jsonify({"status": "deleted", "symbol": symbol})
