import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text

from app.database import Base


class BackupRecord(Base):
    """Tracks all backup operations."""

    __tablename__ = "backup_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    backup_type = Column(String(20), nullable=False)  # basebackup, pgdump, restore
    database_name = Column(String(255), nullable=True)
    status = Column(String(20), nullable=False, default="running")  # running, success, failed
    file_path = Column(Text, nullable=True)
    size_bytes = Column(Integer, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    source_host = Column(String(255), nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    verified_at = Column(DateTime, nullable=True)


class JobHistory(Base):
    """Tracks all scheduled job executions."""

    __tablename__ = "job_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_name = Column(String(100), nullable=False)
    job_type = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False, default="running")
    output = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)


class JobSchedule(Base):
    """Stores configurable job schedules."""

    __tablename__ = "job_schedules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_name = Column(String(100), unique=True, nullable=False)
    job_type = Column(String(50), nullable=False)
    cron_expression = Column(String(100), nullable=False)
    is_enabled = Column(Boolean, default=True)
    description = Column(Text, nullable=True)
    last_run_at = Column(DateTime, nullable=True)
    last_run_status = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
