"""Backup verification service."""

import datetime
import logging
import os
import subprocess
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)


def _format_size(size_bytes: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def verify_backup(backup_path: str) -> dict:
    """Verify a backup's integrity and return status report."""
    report = {
        "path": backup_path,
        "exists": False,
        "size": 0,
        "age_hours": None,
        "checks": [],
        "overall_status": "unknown",
    }

    path = Path(backup_path)
    if not path.exists():
        report["checks"].append({"name": "existence", "status": "fail", "detail": "Path not found"})
        report["overall_status"] = "fail"
        return report

    report["exists"] = True

    if path.is_dir():
        size = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
    else:
        size = path.stat().st_size
    report["size"] = size

    if size == 0:
        report["checks"].append({"name": "size", "status": "fail", "detail": "Backup is empty"})
    else:
        report["checks"].append({"name": "size", "status": "pass", "detail": f"{_format_size(size)}"})

    mtime = datetime.datetime.fromtimestamp(path.stat().st_mtime)
    age = datetime.datetime.now() - mtime
    report["age_hours"] = round(age.total_seconds() / 3600, 1)

    max_age = settings.BACKUP_RETENTION_DAYS * 24
    if age.total_seconds() > max_age * 3600:
        report["checks"].append({"name": "age", "status": "warn", "detail": f"{report['age_hours']}h old (max {max_age}h)"})
    else:
        report["checks"].append({"name": "age", "status": "pass", "detail": f"{report['age_hours']}h old"})

    pg_restore = os.path.join(settings.PG_BIN_DIR, "pg_restore")
    if path.is_file() and path.suffix == ".dump":
        try:
            result = subprocess.run(
                [pg_restore, "--list", str(path)],
                capture_output=True, text=True, timeout=60,
            )
            if result.returncode == 0:
                line_count = len(result.stdout.strip().split("\n"))
                report["checks"].append({"name": "integrity", "status": "pass", "detail": f"TOC: {line_count} entries"})
            else:
                report["checks"].append({"name": "integrity", "status": "fail", "detail": result.stderr[:500]})
        except Exception as e:
            report["checks"].append({"name": "integrity", "status": "warn", "detail": f"Could not verify: {e}"})
    elif path.is_dir():
        expected_files = ["base.tar.gz", "pg_wal.tar.gz", "backup_manifest"]
        found = [f for f in expected_files if (path / f).exists()]
        if found:
            report["checks"].append({"name": "integrity", "status": "pass", "detail": f"Found: {', '.join(found)}"})
        else:
            actual = [f.name for f in path.iterdir()][:10]
            report["checks"].append({"name": "integrity", "status": "warn", "detail": f"Files: {', '.join(actual)}"})

    statuses = [c["status"] for c in report["checks"]]
    if "fail" in statuses:
        report["overall_status"] = "fail"
    elif "warn" in statuses:
        report["overall_status"] = "warn"
    else:
        report["overall_status"] = "pass"

    return report


def verify_all_backups() -> dict:
    """Verify all backups on disk and return summary."""
    results = {"basebackups": [], "pgdumps": [], "summary": {}}

    base_dir = Path(settings.basebackup_dir)
    if base_dir.is_dir():
        for entry in sorted(base_dir.iterdir(), reverse=True):
            if entry.is_dir() and entry.name.startswith("basebackup_"):
                results["basebackups"].append(verify_backup(str(entry)))

    dump_dir = Path(settings.pgdump_dir)
    if dump_dir.is_dir():
        for ts_dir in sorted(dump_dir.iterdir(), reverse=True):
            if ts_dir.is_dir():
                for dump_file in ts_dir.glob("*.dump"):
                    results["pgdumps"].append(verify_backup(str(dump_file)))

    total = len(results["basebackups"]) + len(results["pgdumps"])
    passed = sum(
        1 for r in results["basebackups"] + results["pgdumps"]
        if r["overall_status"] == "pass"
    )
    results["summary"] = {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "verified_at": datetime.datetime.utcnow().isoformat(),
    }
    return results
