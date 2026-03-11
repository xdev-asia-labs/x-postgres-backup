"""Backup service - handles pg_basebackup and pg_dump operations."""

import datetime
import logging
import os
import shutil
import subprocess
import time
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import settings
from app.models import BackupRecord
from app.services.cluster import get_cluster_status
from app.services.notification import notify_backup_status

logger = logging.getLogger(__name__)


def _get_dir_size(path: str) -> int:
    total = 0
    for dirpath, _dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.isfile(fp):
                total += os.path.getsize(fp)
    return total


def _format_size(size_bytes: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


async def run_basebackup(db: Session) -> BackupRecord:
    """Run pg_basebackup from the current leader node."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    backup_name = f"basebackup_{timestamp}"
    backup_path = os.path.join(settings.basebackup_dir, backup_name)

    record = BackupRecord(
        backup_type="basebackup",
        status="running",
        file_path=backup_path,
        started_at=datetime.datetime.utcnow(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    try:
        status = await get_cluster_status()
        if not status.leader:
            raise RuntimeError("No cluster leader found")

        record.source_host = status.leader.host
        db.commit()

        os.makedirs(backup_path, exist_ok=True)

        pg_basebackup = os.path.join(settings.PG_BIN_DIR, "pg_basebackup")
        cmd = [
            pg_basebackup,
            "-h", status.leader.host,
            "-p", str(settings.PG_PORT),
            "-U", settings.PG_REPLICATION_USER,
            "-D", backup_path,
            "-Ft", "-z", "-Xs", "-P",
            "--label", backup_name,
        ]

        env = os.environ.copy()
        env["PGPASSWORD"] = settings.PG_REPLICATION_PASSWORD

        start = time.time()
        result = subprocess.run(
            cmd, capture_output=True, text=True, env=env, timeout=7200
        )
        elapsed = time.time() - start

        if result.returncode != 0:
            raise RuntimeError(result.stderr)

        size = _get_dir_size(backup_path)
        record.status = "success"
        record.size_bytes = size
        record.duration_seconds = elapsed
        record.finished_at = datetime.datetime.utcnow()

    except Exception as e:
        record.status = "failed"
        record.error_message = str(e)[:2000]
        record.finished_at = datetime.datetime.utcnow()
        logger.exception("pg_basebackup failed")

    db.commit()
    db.refresh(record)

    # Send notification
    await notify_backup_status(
        backup_type="basebackup",
        status=record.status,
        source_host=record.source_host,
        size=_format_size(record.size_bytes) if record.size_bytes else None,
        duration=record.duration_seconds,
        error=record.error_message,
    )
    return record


async def run_pgdump(db: Session, database: str | None = None) -> list[BackupRecord]:
    """Run pg_dump for one or all databases."""
    status = await get_cluster_status()
    if not status.leader:
        raise RuntimeError("No cluster leader found")

    leader_host = status.leader.host
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    dump_dir = os.path.join(settings.pgdump_dir, timestamp)
    os.makedirs(dump_dir, exist_ok=True)

    pg_dump = os.path.join(settings.PG_BIN_DIR, "pg_dump")
    psql = os.path.join(settings.PG_BIN_DIR, "psql")
    env = os.environ.copy()
    env["PGPASSWORD"] = settings.PG_PASSWORD

    if database:
        databases = [database]
    else:
        result = subprocess.run(
            [
                psql, "-h", leader_host, "-p", str(settings.PG_PORT),
                "-U", settings.PG_USER, "-Atc",
                "SELECT datname FROM pg_database WHERE datistemplate = false AND datname NOT IN ('postgres');",
            ],
            capture_output=True, text=True, env=env, timeout=30,
        )
        databases = [d.strip() for d in result.stdout.strip().split("\n") if d.strip()]

    records = []
    for db_name in databases:
        dump_file = os.path.join(dump_dir, f"{db_name}_backup_{timestamp}.dump")
        record = BackupRecord(
            backup_type="pgdump",
            database_name=db_name,
            status="running",
            file_path=dump_file,
            source_host=leader_host,
            started_at=datetime.datetime.utcnow(),
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        try:
            start = time.time()
            result = subprocess.run(
                [
                    pg_dump, "-h", leader_host, "-p", str(settings.PG_PORT),
                    "-U", settings.PG_USER, "-Fc",
                    "--no-owner", "--no-privileges",
                    "-f", dump_file, db_name,
                ],
                capture_output=True, text=True, env=env, timeout=7200,
            )
            elapsed = time.time() - start

            if result.returncode != 0:
                raise RuntimeError(result.stderr)

            size = os.path.getsize(dump_file) if os.path.exists(dump_file) else 0
            record.status = "success"
            record.size_bytes = size
            record.duration_seconds = elapsed
            record.finished_at = datetime.datetime.utcnow()

        except Exception as e:
            record.status = "failed"
            record.error_message = str(e)[:2000]
            record.finished_at = datetime.datetime.utcnow()
            logger.exception("pg_dump failed for %s", db_name)

        db.commit()
        db.refresh(record)

        # Send notification for each database backup
        await notify_backup_status(
            backup_type="pgdump",
            status=record.status,
            database_name=record.database_name,
            source_host=record.source_host,
            size=_format_size(record.size_bytes) if record.size_bytes else None,
            duration=record.duration_seconds,
            error=record.error_message,
        )

        records.append(record)

    return records


def list_backups() -> list[dict]:
    """List physical backup directories on disk."""
    base_dir = settings.basebackup_dir
    backups = []
    if not os.path.isdir(base_dir):
        return backups

    for entry in sorted(Path(base_dir).iterdir(), reverse=True):
        if entry.is_dir() and entry.name.startswith("basebackup_"):
            size = _get_dir_size(str(entry))
            mtime = datetime.datetime.fromtimestamp(entry.stat().st_mtime)
            backups.append({
                "name": entry.name,
                "path": str(entry),
                "type": "basebackup",
                "size": size,
                "size_human": _format_size(size),
                "created_at": mtime.isoformat(),
            })
    return backups


def list_dumps() -> list[dict]:
    """List logical backup directories on disk."""
    dump_dir = settings.pgdump_dir
    dumps = []
    if not os.path.isdir(dump_dir):
        return dumps

    for entry in sorted(Path(dump_dir).iterdir(), reverse=True):
        if entry.is_dir():
            files = list(entry.glob("*.dump"))
            total_size = sum(f.stat().st_size for f in files)
            mtime = datetime.datetime.fromtimestamp(entry.stat().st_mtime)
            dumps.append({
                "name": entry.name,
                "path": str(entry),
                "type": "pgdump",
                "database_count": len(files),
                "databases": [f.stem.replace(f"_backup_{entry.name}", "") for f in files],
                "size": total_size,
                "size_human": _format_size(total_size),
                "created_at": mtime.isoformat(),
            })
    return dumps


def get_disk_usage() -> dict:
    """Get disk usage info for backup directory."""
    backup_dir = settings.BACKUP_DIR
    if not os.path.isdir(backup_dir):
        return {"total": 0, "used": 0, "free": 0, "percent": 0}

    stat = shutil.disk_usage(backup_dir)
    return {
        "total": stat.total,
        "used": stat.used,
        "free": stat.free,
        "percent": round(stat.used / stat.total * 100, 1),
        "total_human": _format_size(stat.total),
        "used_human": _format_size(stat.used),
        "free_human": _format_size(stat.free),
    }


def cleanup_old_backups() -> dict:
    """Remove backups older than retention period."""
    removed = {"basebackup": 0, "pgdump": 0}
    cutoff = datetime.datetime.now() - datetime.timedelta(days=settings.BACKUP_RETENTION_DAYS)

    base_dir = Path(settings.basebackup_dir)
    if base_dir.is_dir():
        dirs = sorted(base_dir.iterdir())
        while len(dirs) > settings.BACKUP_RETENTION_COPIES:
            oldest = dirs.pop(0)
            mtime = datetime.datetime.fromtimestamp(oldest.stat().st_mtime)
            if mtime < cutoff:
                shutil.rmtree(oldest)
                removed["basebackup"] += 1

    dump_dir = Path(settings.pgdump_dir)
    if dump_dir.is_dir():
        dirs = sorted(dump_dir.iterdir())
        while len(dirs) > settings.BACKUP_RETENTION_COPIES:
            oldest = dirs.pop(0)
            mtime = datetime.datetime.fromtimestamp(oldest.stat().st_mtime)
            if mtime < cutoff:
                shutil.rmtree(oldest)
                removed["pgdump"] += 1

    return removed
