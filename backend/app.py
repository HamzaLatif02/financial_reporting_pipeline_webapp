import eventlet          # must be first — patches sockets before any other import
eventlet.monkey_patch()
import atexit
import logging
import os
from pathlib import Path

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_smorest import Api
from dotenv import load_dotenv

from api.assets     import assets_bp
from api.pipeline   import pipeline_bp
from api.reports    import reports_bp
from api.schedule   import schedule_bp
from api.comparison import comparison_bp
from api.cache      import cache_bp
from extensions     import limiter
from docs_config    import OPENAPI_CONFIG

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_ENV       = os.getenv("FLASK_ENV", "development")
_IS_PROD   = _ENV == "production"
_BUILD_DIR = Path(__file__).parent.parent / "frontend" / "build"

if _IS_PROD:
    app = Flask(__name__, static_folder=str(_BUILD_DIR), static_url_path="/")
    _allowed_origins = [
        os.getenv("RENDER_EXTERNAL_URL", "https://finpipe.xyz"),
        "https://finpipe.xyz",
        "https://www.finpipe.xyz",
    ]
    CORS(app, resources={r"/api/*": {"origins": _allowed_origins}})
    logger.info("Production mode — serving React build from %s", _BUILD_DIR)
else:
    app = Flask(__name__)
    CORS(app)
    logger.info("Development mode — CORS enabled, React served by Vite")

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
app.config.update(OPENAPI_CONFIG)

socketio = SocketIO(
    app,
    cors_allowed_origins=_allowed_origins if _IS_PROD else "*",
    async_mode="eventlet",
    logger=False,
    engineio_logger=False,
    ping_timeout=120,    # seconds — outlasts AI analysis calls
    ping_interval=25,    # send ping every 25 s to keep Render proxy alive
)

limiter.init_app(app)

api = Api(app)
api.register_blueprint(assets_bp,      url_prefix="/api/assets")
api.register_blueprint(pipeline_bp,    url_prefix="/api/pipeline")
api.register_blueprint(reports_bp,     url_prefix="/api/reports")
api.register_blueprint(schedule_bp,    url_prefix="/api/schedule")
api.register_blueprint(comparison_bp,  url_prefix="/api/comparison")
api.register_blueprint(cache_bp,       url_prefix="/api/cache")


@app.errorhandler(429)
def ratelimit_handler(e):
    retry_after = None
    try:
        retry_after = int(e.description.split("in")[1].split("second")[0].strip())
    except Exception:
        pass
    from flask import jsonify as _jsonify
    return _jsonify({
        "error":       "rate_limit_exceeded",
        "message":     str(e.description),
        "retry_after": retry_after,
    }), 429


@app.get("/api/health")
def health():
    from scheduler import _scheduler, start_scheduler
    if not _scheduler.running:
        logger.warning("Health check: scheduler stopped — restarting")
        start_scheduler()
    return jsonify({"status": "ok", "scheduler_running": _scheduler.running})


if _IS_PROD:
    @app.get("/")
    def index():
        return send_from_directory(str(_BUILD_DIR), "index.html")

    @app.errorhandler(404)
    def catch_all(e):
        return send_from_directory(str(_BUILD_DIR), "index.html")


# ── Scheduler lifecycle ───────────────────────────────────────────────────────
from scheduler import start_scheduler, shutdown_scheduler  # noqa: E402
from db import init_db  # noqa: E402

# Call unconditionally at module level so it runs whenever this module is
# imported — which is exactly what Gunicorn does.  start_scheduler() guards
# against double-start internally (if _scheduler.running: return).
with app.app_context():
    init_db()
    from db import init_cache_table, purge_expired_cache  # noqa: E402
    init_cache_table()
    purge_expired_cache()
    start_scheduler()

atexit.register(shutdown_scheduler)

# Import socket handlers AFTER socketio is defined (avoids circular import)
import socket_handlers  # noqa: F401, E402

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5001, debug=True)
