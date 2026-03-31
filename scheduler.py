import json
import logging
import time
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

import pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s",
    force=True,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("data/pipeline.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

CONFIG_DIR = Path("data")
SCHEDULE_HOUR   = 7
SCHEDULE_MINUTE = 30


def _load_configs() -> list:
    """Scan data/ for *_config.json files and return a list of config dicts."""
    paths = sorted(CONFIG_DIR.glob("*_config.json"))
    configs = []
    for path in paths:
        try:
            with open(path) as f:
                config = json.load(f)
            configs.append((path.name, config))
            logger.info("Found config: %s  (%s)", path.name, config.get("symbol", "?"))
        except Exception as exc:
            logger.warning("Could not load %s: %s", path.name, exc)
    return configs


def _make_job(config: dict):
    """Return a zero-argument callable that runs the pipeline for this config."""
    symbol = config["symbol"]

    def job():
        logger.info("Scheduled run starting for %s.", symbol)
        try:
            pipeline.run_pipeline(config)
        except SystemExit:
            # pipeline.run_pipeline calls sys.exit(1) on fatal errors;
            # catch it here so one job failure doesn't kill the scheduler.
            logger.error("Pipeline exited with error for %s.", symbol)

    job.__name__ = f"pipeline_{symbol}"
    return job


def start_scheduler() -> None:
    """Scan for configs, schedule each one, and keep the process alive."""
    logger.info("=" * 56)
    logger.info("  Financial Reporting Scheduler  (APScheduler %s)",
                __import__("apscheduler").__version__)
    logger.info("  Schedule: Mon-Fri at %02d:%02d", SCHEDULE_HOUR, SCHEDULE_MINUTE)
    logger.info("=" * 56)

    configs = _load_configs()
    if not configs:
        logger.warning(
            "No *_config.json files found in %s. "
            "Run 'python pipeline.py' interactively first to create one.",
            CONFIG_DIR,
        )

    scheduler = BackgroundScheduler()

    trigger = CronTrigger(
        day_of_week="mon-fri",
        hour=SCHEDULE_HOUR,
        minute=SCHEDULE_MINUTE,
    )

    for filename, config in configs:
        symbol = config.get("symbol", filename)
        scheduler.add_job(
            func=_make_job(config),
            trigger=trigger,
            id=f"pipeline_{symbol}",
            name=f"{config.get('name', symbol)} ({symbol})",
            replace_existing=True,
        )

    scheduler.start()

    # next_run_time is only populated after start()
    for job in scheduler.get_jobs():
        next_run = job.next_run_time
        logger.info(
            "Scheduled: %-30s | next run: %s",
            job.name,
            next_run.strftime("%Y-%m-%d %H:%M %Z") if next_run else "N/A",
        )

    logger.info("Scheduler running. Press Ctrl+C to stop.")

    try:
        heartbeat = 0
        while True:
            time.sleep(60)
            heartbeat += 1
            if heartbeat % 5 == 0:
                jobs = scheduler.get_jobs()
                for job in jobs:
                    next_run = job.next_run_time
                    logger.info(
                        "Heartbeat — %s | next run: %s",
                        job.name,
                        next_run.strftime("%Y-%m-%d %H:%M %Z") if next_run else "N/A",
                    )
    except KeyboardInterrupt:
        logger.info("Interrupt received — shutting down scheduler.")
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped. Goodbye.")


if __name__ == "__main__":
    start_scheduler()
