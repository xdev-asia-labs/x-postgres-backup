"""Restore service - handles pg_restore and base restore operations."""

import datetime
import logging
import os
import subprocess
import time
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import settings
from app.models import BackupRecord
from app.services.cluster import get_cluster_status

logger = logging.getLogger(__name__)


def _format_size(size_bytes: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


async def restore_pgdump(
    db: Session, dump_file: str, target_database: str,
    target_host: str | None = None, drop_existing: bool = False,
) -> BackupRecord:
    """Restore a pg_dump file to a target database."""
    if not os.path.isfile(dump_file):
        raise FileNotFoundError(f"Dump file not found: {dump_file}")

    if not target_host:
        status = await get_cluster_status()
        if not status.leader:
            raise RuntimeError("No cluster leader found")
        target_host = status.leader.host

    record = BackupRecord(
        backup_type="restore",
        database_name=target_database,
        status="running",
        file_path=dump_file,
        source_host=target_host,
        started_at=datetime.datetime.utcnow(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    pg_restore = os.path.join(settings.PG_BIN_DIR, "pg_restore")
    psql = os.path.join(settings.PG_BIN_DIR, "psql")
    env = os.environ.copy()
    env["PGPASSWORD"] = settings.PG_PASSWORD

    try:
        subprocess.run(
            [
                psql, "-h", target_host, "-p", str(settings.PG_PORT),
                "-U", settings.PG_USER, "-tc",
                f"SELECT 1 FROM pg_database WHERE datname = '{target_database}';",
            ],
            capture_output=True, text=True, env=env, timeout=30,
        )

        create_result = subprocess.run(
            [
                psql, "-h", target_host, "-p", str(settings.PG_PORT),
                "-U", settings.PG_USER, "-c",
                f"CREATE DATABASE \"{target_database}\";",
            ],
            capture_output=True, text=True, env=env, timeout=30,
        )
        if create_result.returncode != 0 and "already exists" not in create_result.stderr:
            logger.warning("Create DB warning: %s", create_result.stderr)

        cmd = [
            pg_restore, "-h", target_host, "-p", str(settings.PG_PORT),
            "-U", settings.PG_USER, "-d", target_database,
            "--no-owner", "--no-privileges", "-v",
        ]
        if drop_existing:
            cmd.append("--clean")
        cmd.append(dump_file)

        start = time.time()
        result = subprocess.run(
            cmd, capture_output=True, text=True, env=env, timeout=7200,
        )
        elapsed = time.time() - start

        if result.returncode != 0 and "errors ignored" not in result.stderr:
            raise RuntimeError(result.stderr[-2000:])

        record.status = "success"
        record.duration_seconds = elapsed
        record.finished_at = datetime.datetime.utcnow()

    except Exception as e:
        record.status = "failed"
        record.error_message = str(e)[:2000]
        record.finished_at = datetime.datetime.utcnow()
        logger.exception("pg_restore failed for %s", target_database)

    db.commit()
    db.refresh(record)
    return record


def list_restorable_dumps() -> list[dict]:
    """List all available dump files that can be restored."""
    dump_dir = Path(settings.pgdump_dir)
    items = []
    if not dump_dir.is_dir():
        return items

    for ts_dir in sorted(dump_dir.iterdir(), reverse=True):
        if not ts_dir.is_dir():
            continue
        for dump_file in sorted(ts_dir.glob("*.dump")):
            mtime = datetime.datetime.fromtimestamp(dump_file.stat().st_mtime)
            size = dump_file.stat().st_size
            name_parts = dump_file.stem.rsplit("_backup_", 1)
            db_name = name_parts[0] if len(name_parts) > 1 else dump_file.stem
            items.append({
                "file": str(dump_file),
                "database": db_name,
                "timestamp": ts_dir.name,
                "size": size,
                "size_human": _format_size(size),
                "modified_at": mtime.isoformat(),
            })
    return items


def list_restorable_basebackups() -> list[dict]:
    """List all available base backups that can be restored."""
    base_dir = Path(settings.basebackup_dir)
    items = []
    if not base_dir.is_dir():
        return items

    for entry in sorted(base_dir.iterdir(), reverse=True):
        if entry.is_dir() and entry.name.startswith("basebackup_"):
            mtime = datetime.datetime.fromtimestamp(entry.stat().st_mtime)
            size = sum(f.stat().st_size for f in entry.rglob("*") if f.is_file())
            items.append({
                "name": entry.name,
                "path": str(entry),
                "size": size,
                "size_human": _format_size(size),
                "modified_at": mtime.isoformat(),
            })
    return items
