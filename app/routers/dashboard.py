"""Dashboard HTML routes - serves Jinja2 templates."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import BackupRecord, JobHistory, JobSchedule
from app.services import backup as backup_svc
from app.services import cluster as cluster_svc
from app.services import restore as restore_svc

router = APIRouter(tags=["dashboard"])


def _ctx(request: Request, **kwargs) -> dict:
    """Build template context with i18n support."""
    return {
        "request": request,
        "_": request.state._,
        "lang": request.state.lang,
        **kwargs,
    }


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page."""
    return request.app.state.templates.TemplateResponse(
        "login.html",
        _ctx(request),
    )


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    try:
        cluster = await cluster_svc.get_cluster_status()
    except Exception:
        cluster = None

    recent_backups = (
        db.query(BackupRecord)
        .order_by(BackupRecord.started_at.desc())
        .limit(10)
        .all()
    )
    recent_jobs = (
        db.query(JobHistory)
        .order_by(JobHistory.started_at.desc())
        .limit(5)
        .all()
    )
    disk = backup_svc.get_disk_usage()
    schedules = db.query(JobSchedule).all()

    return request.app.state.templates.TemplateResponse(
        "dashboard.html",
        _ctx(
            request,
            cluster=cluster,
            recent_backups=recent_backups,
            recent_jobs=recent_jobs,
            disk=disk,
            schedules=schedules,
            page="dashboard",
        ),
    )


@router.get("/backups", response_class=HTMLResponse)
async def backups_page(request: Request, db: Session = Depends(get_db)):
    records = (
        db.query(BackupRecord)
        .order_by(BackupRecord.started_at.desc())
        .limit(100)
        .all()
    )
    on_disk = {
        "basebackups": backup_svc.list_backups(),
        "pgdumps": backup_svc.list_dumps(),
    }
    disk = backup_svc.get_disk_usage()

    return request.app.state.templates.TemplateResponse(
        "backups.html",
        _ctx(
            request,
            records=records,
            on_disk=on_disk,
            disk=disk,
            page="backups",
        ),
    )


@router.get("/restore", response_class=HTMLResponse)
async def restore_page(request: Request):
    dumps = restore_svc.list_restorable_dumps()
    basebackups = restore_svc.list_restorable_basebackups()

    try:
        databases = await cluster_svc.get_databases()
    except Exception:
        databases = []

    return request.app.state.templates.TemplateResponse(
        "restore.html",
        _ctx(
            request,
            dumps=dumps,
            basebackups=basebackups,
            databases=databases,
            page="restore",
        ),
    )


@router.get("/jobs", response_class=HTMLResponse)
def jobs_page(request: Request, db: Session = Depends(get_db)):
    schedules = db.query(JobSchedule).all()
    history = (
        db.query(JobHistory)
        .order_by(JobHistory.started_at.desc())
        .limit(50)
        .all()
    )
    return request.app.state.templates.TemplateResponse(
        "jobs.html",
        _ctx(
            request,
            schedules=schedules,
            history=history,
            page="jobs",
        ),
    )


@router.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request, db: Session = Depends(get_db)):
    from app.config import settings as app_settings

    schedules = db.query(JobSchedule).all()
    disk = backup_svc.get_disk_usage()

    return request.app.state.templates.TemplateResponse(
        "settings.html",
        _ctx(
            request,
            settings=app_settings,
            schedules=schedules,
            disk=disk,
            page="settings",
        ),
    )
