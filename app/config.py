import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    # App
    APP_NAME: str = os.getenv("APP_NAME", "x-postgres-backup")
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))
    APP_LOG_LEVEL: str = os.getenv("APP_LOG_LEVEL", "info")
    APP_SECRET_KEY: str = os.getenv("APP_SECRET_KEY", "change-me")

    # Patroni
    PATRONI_NODES: list[str] = [
        n.strip()
        for n in os.getenv("PATRONI_NODES", "10.10.10.11:8008").split(",")
    ]
    PATRONI_AUTH_ENABLED: bool = os.getenv("PATRONI_AUTH_ENABLED", "false").lower() == "true"
    PATRONI_AUTH_USERNAME: str = os.getenv("PATRONI_AUTH_USERNAME", "")
    PATRONI_AUTH_PASSWORD: str = os.getenv("PATRONI_AUTH_PASSWORD", "")

    # PostgreSQL
    PG_PORT: int = int(os.getenv("PG_PORT", "5432"))
    PG_USER: str = os.getenv("PG_USER", "postgres")
    PG_PASSWORD: str = os.getenv("PG_PASSWORD", "")
    PG_BIN_DIR: str = os.getenv("PG_BIN_DIR", "/usr/lib/postgresql/18/bin")

    # Replication
    PG_REPLICATION_USER: str = os.getenv("PG_REPLICATION_USER", "replicator")
    PG_REPLICATION_PASSWORD: str = os.getenv("PG_REPLICATION_PASSWORD", "")

    # Backup
    BACKUP_DIR: str = os.getenv("BACKUP_DIR", "/var/backups/postgresql")
    BACKUP_RETENTION_DAYS: int = int(os.getenv("BACKUP_RETENTION_DAYS", "7"))
    BACKUP_RETENTION_COPIES: int = int(os.getenv("BACKUP_RETENTION_COPIES", "7"))
    BACKUP_COMPRESSION: str = os.getenv("BACKUP_COMPRESSION", "gzip")

    # Schedules (cron expressions)
    SCHEDULE_BASEBACKUP: str = os.getenv("SCHEDULE_BASEBACKUP", "0 2 * * *")
    SCHEDULE_PGDUMP: str = os.getenv("SCHEDULE_PGDUMP", "0 3 * * *")
    SCHEDULE_VERIFY: str = os.getenv("SCHEDULE_VERIFY", "0 4 * * *")
    SCHEDULE_CLEANUP: str = os.getenv("SCHEDULE_CLEANUP", "0 6 * * *")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///data/backup_manager.db")

    @property
    def basebackup_dir(self) -> str:
        return os.path.join(self.BACKUP_DIR, "basebackup")

    @property
    def pgdump_dir(self) -> str:
        return os.path.join(self.BACKUP_DIR, "pg_dump")

    @property
    def logs_dir(self) -> str:
        return os.path.join(self.BACKUP_DIR, "logs")

    @property
    def debug(self) -> bool:
        return self.APP_LOG_LEVEL.lower() == "debug"


settings = Settings()
