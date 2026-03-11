"""APScheduler integration for background backup jobs."""

import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import settings
from app.database import SessionLocal
from app.models import JobHistory, JobSchedule

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def _run_job(job_name: str, job_type: str, func):
    """Wrapper to run a job and record history."""
    db = SessionLocal()
    history = JobHistory(
        job_name=job_name,
        job_type=job_type,
        status="running",
        started_at=datetime.utcnow(),
    )
    db.add(history)
    db.commit()
    db.refresh(history)

    try:
        result = await func(db) if job_type != "cleanup" else func()
        history.status = "success"
        if isinstance(result, dict):
            history.output = str(result)[:5000]
        elif isinstance(result, list):
            history.output = f"Completed {len(result)} items"
    except Exception as e:
        history.status = "failed"
        history.output = str(e)[:5000]
        logger.exception("Job %s failed", job_name)
    finally:
        history.finished_at = datetime.utcnow()
        schedule = db.query(JobSchedule).filter(JobSchedule.job_name == job_name).first()
        if schedule:
            schedule.last_run_at = datetime.utcnow()
            schedule.last_run_status = history.status
        db.commit()
        db.close()


async def job_basebackup():
    from app.services.backup import run_basebackup
    await _run_job("basebackup", "basebackup", run_basebackup)


async def job_pgdump():
    from app.services.backup import run_pgdump
    await _run_job("pgdump", "pgdump", run_pgdump)


async def job_cleanup():
    from app.services.backup import cleanup_old_backups
    await _run_job("cleanup", "cleanup", lambda db: cleanup_old_backups())


async def job_verify():
    from app.services.verify import verify_all_backups
    await _run_job("verify", "verify", lambda db: verify_all_backups())


def init_default_schedules():
    """Ensure default job schedules exist in the database."""
    db = SessionLocal()
    try:
        defaults = [
            {
                "job_name": "basebackup",
                "job_type": "basebackup",
                "cron_expression": settings.SCHEDULE_BASEBACKUP,
                "is_enabled": True,
                "description": "Full physical backup via pg_basebackup",
            },
            {
                "job_name": "pgdump",
                "job_type": "pgdump",
                "cron_expression": settings.SCHEDULE_PGDUMP,
                "is_enabled": True,
                "description": "Logical backup via pg_dump for each database",
            },
            {
                "job_name": "cleanup",
                "job_type": "cleanup",
                "cron_expression": settings.SCHEDULE_CLEANUP,
                "is_enabled": True,
                "description": "Remove old backups beyond retention period",
            },
            {
                "job_name": "verify",
                "job_type": "verify",
                "cron_expression": settings.SCHEDULE_VERIFY,
                "is_enabled": True,
                "description": "Verify backup integrity",
            },
        ]
        for d in defaults:
            existing = db.query(JobSchedule).filter(JobSchedule.job_name == d["job_name"]).first()
            if not existing:
                db.add(JobSchedule(**d))
        db.commit()
    finally:
        db.close()


JOB_MAP = {
    "basebackup": job_basebackup,
    "pgdump": job_pgdump,
    "cleanup": job_cleanup,
    "verify": job_verify,
}


def sync_scheduler_from_db():
    """Load schedules from DB and register with APScheduler."""
    scheduler.remove_all_jobs()

    db = SessionLocal()
    try:
        schedules = db.query(JobSchedule).filter(JobSchedule.is_enabled.is_(True)).all()
        for s in schedules:
            func = JOB_MAP.get(s.job_name)
            if not func:
                logger.warning("Unknown job: %s", s.job_name)
                continue
            try:
                parts = s.cron_expression.split()
                if len(parts) == 5:
                    trigger = CronTrigger(
                        minute=parts[0], hour=parts[1], day=parts[2],
                        month=parts[3], day_of_week=parts[4],
                    )
                    scheduler.add_job(func, trigger, id=s.job_name, replace_existing=True)
                    logger.info("Scheduled job: %s (%s)", s.job_name, s.cron_expression)
            except Exception:
                logger.exception("Failed to schedule job: %s", s.job_name)
    finally:
        db.close()


def start_scheduler():
    """Initialize schedules and start the scheduler."""
    init_default_schedules()
    sync_scheduler_from_db()
    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler started")


def stop_scheduler():
    """Shutdown the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
