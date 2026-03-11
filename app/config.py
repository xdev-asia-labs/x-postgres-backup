import os
import secrets

from dotenv import load_dotenv

load_dotenv()


def _generate_secret(env_var: str) -> str:
    """Return env value or generate a random secret for development."""
    value = os.getenv(env_var, "")
    if not value:
        import logging
        logging.getLogger(__name__).warning(
            f"{env_var} not set! Using auto-generated secret. Set it in .env for production."
        )
        return secrets.token_urlsafe(32)
    return value


class Settings:
    # App
    APP_NAME: str = os.getenv("APP_NAME", "x-postgres-backup")
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))
    APP_LOG_LEVEL: str = os.getenv("APP_LOG_LEVEL", "info")
    APP_SECRET_KEY: str = _generate_secret("APP_SECRET_KEY")

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
    PG_VERSION: str = os.getenv("PG_VERSION", "18")
    PG_BIN_DIR: str = os.getenv(
        "PG_BIN_DIR",
        f"/usr/lib/postgresql/{os.getenv('PG_VERSION', '18')}/bin",
    )

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

    # Telegram Notifications
    TELEGRAM_ENABLED: bool = os.getenv("TELEGRAM_ENABLED", "false").lower() == "true"
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")

    # Email Notifications
    EMAIL_ENABLED: bool = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
    EMAIL_SMTP_HOST: str = os.getenv("EMAIL_SMTP_HOST", "smtp.gmail.com")
    EMAIL_SMTP_PORT: int = int(os.getenv("EMAIL_SMTP_PORT", "587"))
    EMAIL_SMTP_USER: str = os.getenv("EMAIL_SMTP_USER", "")
    EMAIL_SMTP_PASSWORD: str = os.getenv("EMAIL_SMTP_PASSWORD", "")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "")
    EMAIL_TO: list[str] = [
        e.strip()
        for e in os.getenv("EMAIL_TO", "").split(",")
        if e.strip()
    ]
    EMAIL_USE_TLS: bool = os.getenv("EMAIL_USE_TLS", "true").lower() == "true"

    # Authentication & Authorization
    AUTH_ENABLED: bool = os.getenv("AUTH_ENABLED", "true").lower() == "true"
    JWT_SECRET_KEY: str = _generate_secret("JWT_SECRET_KEY")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 hours
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "30"))
    
    # Session
    SESSION_SECRET_KEY: str = _generate_secret("SESSION_SECRET_KEY")
    SESSION_COOKIE_NAME: str = os.getenv("SESSION_COOKIE_NAME", "xpb_session")
    SESSION_MAX_AGE: int = int(os.getenv("SESSION_MAX_AGE", "86400"))  # 24 hours

    # OAuth2 - Google SSO
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")

    # OAuth2 - Microsoft SSO
    MICROSOFT_CLIENT_ID: str = os.getenv("MICROSOFT_CLIENT_ID", "")
    MICROSOFT_CLIENT_SECRET: str = os.getenv("MICROSOFT_CLIENT_SECRET", "")
    MICROSOFT_TENANT_ID: str = os.getenv("MICROSOFT_TENANT_ID", "common")
    MICROSOFT_REDIRECT_URI: str = os.getenv("MICROSOFT_REDIRECT_URI", "http://localhost:8000/auth/microsoft/callback")

    # User Management
    ALLOW_REGISTRATION: bool = os.getenv("ALLOW_REGISTRATION", "true").lower() == "true"
    DEFAULT_ADMIN_EMAIL: str = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@example.com")
    DEFAULT_ADMIN_PASSWORD: str = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")
    REQUIRE_EMAIL_VERIFICATION: bool = os.getenv("REQUIRE_EMAIL_VERIFICATION", "false").lower() == "true"

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
