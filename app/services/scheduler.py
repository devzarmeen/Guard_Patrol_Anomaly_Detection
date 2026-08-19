from __future__ import annotations

from app.config import app_settings, load_thresholds
from app.database import session_scope
from app.services.pipeline import run_detection_pipeline

_scheduler = None


def _run_job(incremental: bool) -> None:
    with session_scope() as session:
        run_detection_pipeline(
            session,
            incremental=incremental,
            persist=True,
            send_alerts=True,
            method="hybrid",
        )


def start_scheduler() -> None:
    global _scheduler
    settings = app_settings()
    if settings["testing"] or not settings["scheduler_enabled"]:
        return
    if _scheduler is not None:
        return

    from apscheduler.schedulers.background import BackgroundScheduler

    thresholds = load_thresholds()
    sched_cfg = thresholds["scheduler"]
    if not sched_cfg.get("enabled", True):
        return

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        lambda: _run_job(incremental=True),
        "interval",
        seconds=int(sched_cfg.get("incremental_interval_seconds", 60)),
        id="incremental_processing",
        replace_existing=True,
    )
    scheduler.add_job(
        lambda: _run_job(incremental=False),
        "interval",
        minutes=int(sched_cfg.get("batch_interval_minutes", 15)),
        id="batch_processing",
        replace_existing=True,
    )
    scheduler.start()
    _scheduler = scheduler


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
