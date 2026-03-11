"""REST API routes for backup/restore operations."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, get_current_superuser
from app.models import BackupRecord, JobHistory, JobSchedule, User
from app.scheduler import JOB_MAP, sync_scheduler_from_db
from app.services import backup as backup_svc
from app.services import cluster as cluster_svc
from app.services import restore as restore_svc
from app.services import verify as verify_svc
from app.services import settings as settings_svc

router = APIRouter(prefix="/api", tags=["api"])


# --- Pydantic schemas ---

class BackupRequest(BaseModel):
    backup_type: str = "basebackup"
    database: str | None = None


class RestoreRequest(BaseModel):
    dump_file: str
    target_database: str
    target_host: str | None = None
    drop_existing: bool = False


class ScheduleUpdate(BaseModel):
    cron_expression: str | None = None
    is_enabled: bool | None = None


class SettingsUpdate(BaseModel):
    settings: dict[str, str]


# --- Cluster ---

@router.get("/health")
def health_check():
    return {"status": "ok"}


@router.get("/cluster/status")
async def cluster_status(_user: User = Depends(get_current_user)):
    return await cluster_svc.get_cluster_status()


@router.get("/cluster/databases")
async def cluster_databases(_user: User = Depends(get_current_user)):
    return await cluster_svc.get_databases()


# --- Backups ---

@router.get("/backups")
def list_backups(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    records = (
        db.query(BackupRecord)
        .order_by(BackupRecord.started_at.desc())
        .limit(100)
        .all()
    )
    return [_record_to_dict(r) for r in records]


@router.get("/backups/disk")
def list_backups_on_disk(_user: User = Depends(get_current_user)):
    return {
        "basebackups": backup_svc.list_backups(),
        "pgdumps": backup_svc.list_dumps(),
        "disk_usage": backup_svc.get_disk_usage(),
    }


@router.post("/backups/run")
async def run_backup(req: BackupRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    if req.backup_type == "basebackup":
        record = await backup_svc.run_basebackup(db)
    elif req.backup_type == "pgdump":
        records = await backup_svc.run_pgdump(db, req.database)
        return [_record_to_dict(r) for r in records]
    else:
        raise HTTPException(400, "Invalid backup_type. Use 'basebackup' or 'pgdump'")
    return _record_to_dict(record)


@router.get("/backups/{backup_id}")
def get_backup(backup_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    record = db.query(BackupRecord).filter(BackupRecord.id == backup_id).first()
    if not record:
        raise HTTPException(404, "Backup not found")
    return _record_to_dict(record)


# --- Restore ---

@router.get("/restore/available")
def list_restorable(_user: User = Depends(get_current_user)):
    return {
        "dumps": restore_svc.list_restorable_dumps(),
        "basebackups": restore_svc.list_restorable_basebackups(),
    }


@router.post("/restore/run")
async def run_restore(req: RestoreRequest, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    record = await restore_svc.restore_pgdump(
        db, req.dump_file, req.target_database,
        req.target_host, req.drop_existing,
    )
    return _record_to_dict(record)


# --- Verify ---

@router.get("/verify")
def verify_all(_user: User = Depends(get_current_user)):
    return verify_svc.verify_all_backups()


@router.get("/verify/{path:path}")
def verify_single(path: str, _user: User = Depends(get_current_user)):
    return verify_svc.verify_backup(f"/{path}" if not path.startswith("/") else path)


# --- Disk ---

@router.get("/disk")
def disk_usage(_user: User = Depends(get_current_user)):
    return backup_svc.get_disk_usage()


@router.post("/cleanup")
def run_cleanup(_user: User = Depends(get_current_user)):
    return backup_svc.cleanup_old_backups()


# --- Jobs ---

@router.get("/jobs/schedules")
def list_schedules(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return [
        {
            "id": s.id, "job_name": s.job_name, "job_type": s.job_type,
            "cron_expression": s.cron_expression, "is_enabled": s.is_enabled,
            "description": s.description,
            "last_run_at": s.last_run_at.isoformat() if s.last_run_at else None,
            "last_run_status": s.last_run_status,
        }
        for s in db.query(JobSchedule).all()
    ]


@router.put("/jobs/schedules/{schedule_id}")
def update_schedule(schedule_id: int, req: ScheduleUpdate, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    schedule = db.query(JobSchedule).filter(JobSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(404, "Schedule not found")
    if req.cron_expression is not None:
        parts = req.cron_expression.split()
        if len(parts) != 5:
            raise HTTPException(400, "Invalid cron expression (need 5 fields)")
        schedule.cron_expression = req.cron_expression
    if req.is_enabled is not None:
        schedule.is_enabled = req.is_enabled
    db.commit()
    sync_scheduler_from_db()
    return {"status": "updated"}


@router.post("/jobs/run/{job_name}")
async def run_job_now(job_name: str, _user: User = Depends(get_current_user)):
    func = JOB_MAP.get(job_name)
    if not func:
        raise HTTPException(404, f"Unknown job: {job_name}")
    await func()
    return {"status": "executed", "job": job_name}


@router.get("/jobs/history")
def job_history(limit: int = 50, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    records = (
        db.query(JobHistory)
        .order_by(JobHistory.started_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": h.id, "job_name": h.job_name, "job_type": h.job_type,
            "status": h.status, "output": h.output,
            "started_at": h.started_at.isoformat() if h.started_at else None,
            "finished_at": h.finished_at.isoformat() if h.finished_at else None,
        }
        for h in records
    ]


# --- Helpers ---

def _record_to_dict(r: BackupRecord) -> dict:
    return {
        "id": r.id,
        "backup_type": r.backup_type,
        "database_name": r.database_name,
        "status": r.status,
        "file_path": r.file_path,
        "size_bytes": r.size_bytes,
        "duration_seconds": r.duration_seconds,
        "source_host": r.source_host,
        "error_message": r.error_message,
        "started_at": r.started_at.isoformat() if r.started_at else None,
        "finished_at": r.finished_at.isoformat() if r.finished_at else None,
    }


# --- Settings (Admin only) ---

@router.get("/settings")
def get_settings(db: Session = Depends(get_db), _user: User = Depends(get_current_superuser)):
    return settings_svc.get_all_settings(db)


@router.put("/settings")
def update_settings(req: SettingsUpdate, db: Session = Depends(get_db), _user: User = Depends(get_current_superuser)):
    updated = settings_svc.update_settings_bulk(db, req.settings)
    return {"status": "ok", "updated": updated}


@router.get("/settings/{key}")
def get_single_setting(key: str, db: Session = Depends(get_db), _user: User = Depends(get_current_superuser)):
    if key not in settings_svc.ALL_EDITABLE_KEYS:
        raise HTTPException(404, f"Setting '{key}' not found")
    return {"key": key, "value": settings_svc.get_setting(db, key)}
