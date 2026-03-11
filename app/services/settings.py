"""Settings service — read/write app settings from the database.

Settings stored in the DB take precedence over .env defaults.
This allows admins to change cluster connection, backup, schedule, and
notification settings at runtime through the web UI.
"""

import logging

from sqlalchemy.orm import Session

from app.config import settings as env_settings
from app.models import AppSetting

logger = logging.getLogger(__name__)

# Keys that can be edited via admin UI, grouped by category.
EDITABLE_SETTINGS: dict[str, list[dict]] = {
    "cluster": [
        {
            "key": "PATRONI_NODES",
            "desc": "Patroni REST API endpoints (comma-separated)",
        },
        {
            "key": "PATRONI_AUTH_ENABLED",
            "desc": "Enable authentication for Patroni API",
        },
        {"key": "PATRONI_AUTH_USERNAME", "desc": "Patroni API username"},
        {
            "key": "PATRONI_AUTH_PASSWORD",
            "desc": "Patroni API password",
            "secret": True,
        },
    ],
    "postgresql": [
        {"key": "PG_PORT", "desc": "PostgreSQL port"},
        {"key": "PG_USER", "desc": "PostgreSQL superuser"},
        {"key": "PG_PASSWORD", "desc": "PostgreSQL password", "secret": True},
        {"key": "PG_VERSION", "desc": "PostgreSQL major version"},
        {"key": "PG_BIN_DIR", "desc": "Path to PostgreSQL binaries"},
        {"key": "PG_REPLICATION_USER", "desc": "User for pg_basebackup"},
        {
            "key": "PG_REPLICATION_PASSWORD",
            "desc": "Replication password",
            "secret": True,
        },
    ],
    "backup": [
        {"key": "BACKUP_DIR", "desc": "Backup storage directory"},
        {"key": "BACKUP_RETENTION_DAYS", "desc": "Days to retain backups"},
        {"key": "BACKUP_RETENTION_COPIES", "desc": "Minimum backup copies to keep"},
        {"key": "BACKUP_COMPRESSION", "desc": "Compression method (gzip, lz4, zstd)"},
    ],
    "schedule": [
        {"key": "SCHEDULE_BASEBACKUP", "desc": "pg_basebackup cron schedule"},
        {"key": "SCHEDULE_PGDUMP", "desc": "pg_dump cron schedule"},
        {"key": "SCHEDULE_VERIFY", "desc": "Verification cron schedule"},
        {"key": "SCHEDULE_CLEANUP", "desc": "Cleanup cron schedule"},
    ],
    "telegram": [
        {"key": "TELEGRAM_ENABLED", "desc": "Enable Telegram notifications"},
        {"key": "TELEGRAM_BOT_TOKEN", "desc": "Telegram Bot token", "secret": True},
        {"key": "TELEGRAM_CHAT_ID", "desc": "Telegram chat ID"},
    ],
    "email": [
        {"key": "EMAIL_ENABLED", "desc": "Enable email notifications"},
        {"key": "EMAIL_SMTP_HOST", "desc": "SMTP server hostname"},
        {"key": "EMAIL_SMTP_PORT", "desc": "SMTP server port"},
        {"key": "EMAIL_SMTP_USER", "desc": "SMTP username"},
        {"key": "EMAIL_SMTP_PASSWORD", "desc": "SMTP password", "secret": True},
        {"key": "EMAIL_FROM", "desc": "Sender email"},
        {"key": "EMAIL_TO", "desc": "Recipient emails (comma-separated)"},
        {"key": "EMAIL_USE_TLS", "desc": "Use TLS for SMTP"},
    ],
    "sso": [
        {"key": "GOOGLE_CLIENT_ID", "desc": "Google OAuth2 Client ID"},
        {
            "key": "GOOGLE_CLIENT_SECRET",
            "desc": "Google OAuth2 Client Secret",
            "secret": True,
        },
        {"key": "GOOGLE_REDIRECT_URI", "desc": "Google OAuth2 Redirect URI"},
        {"key": "MICROSOFT_CLIENT_ID", "desc": "Microsoft OAuth2 Client ID"},
        {
            "key": "MICROSOFT_CLIENT_SECRET",
            "desc": "Microsoft OAuth2 Client Secret",
            "secret": True,
        },
        {
            "key": "MICROSOFT_TENANT_ID",
            "desc": "Microsoft Tenant ID (common for multi-tenant)",
        },
        {"key": "MICROSOFT_REDIRECT_URI", "desc": "Microsoft OAuth2 Redirect URI"},
    ],
}

# Flat lookup of all editable keys.
ALL_EDITABLE_KEYS: dict[str, dict] = {}
for _cat, _items in EDITABLE_SETTINGS.items():
    for _item in _items:
        ALL_EDITABLE_KEYS[_item["key"]] = {**_item, "category": _cat}


def _env_default(key: str) -> str:
    """Get the default value from the Settings class (loaded from .env)."""
    val = getattr(env_settings, key, "")
    if isinstance(val, list):
        return ",".join(str(v) for v in val)
    if isinstance(val, bool):
        return "true" if val else "false"
    return str(val) if val is not None else ""


def get_setting(db: Session, key: str) -> str:
    """Return a single setting value.  DB value wins over .env default."""
    row = db.query(AppSetting).filter(AppSetting.key == key).first()
    if row is not None:
        return row.value
    return _env_default(key)


def get_all_settings(db: Session) -> dict[str, dict]:
    """Return all editable settings grouped by category.

    Each item contains: key, value, description, category, secret, from_db.
    """
    # Load all DB overrides in one query.
    db_rows = {r.key: r.value for r in db.query(AppSetting).all()}

    result: dict[str, list[dict]] = {}
    for category, items in EDITABLE_SETTINGS.items():
        group = []
        for item in items:
            key = item["key"]
            from_db = key in db_rows
            value = db_rows[key] if from_db else _env_default(key)
            group.append(
                {
                    "key": key,
                    "value": value,
                    "description": item.get("desc", ""),
                    "category": category,
                    "secret": item.get("secret", False),
                    "from_db": from_db,
                }
            )
        result[category] = group
    return result


def update_setting(db: Session, key: str, value: str) -> AppSetting:
    """Create or update a single setting in the database."""
    meta = ALL_EDITABLE_KEYS.get(key)
    if meta is None:
        raise ValueError(f"Setting '{key}' is not editable")

    row = db.query(AppSetting).filter(AppSetting.key == key).first()
    if row:
        row.value = value
    else:
        row = AppSetting(
            key=key,
            value=value,
            description=meta.get("desc", ""),
            category=meta.get("category", "general"),
        )
        db.add(row)
    db.commit()
    db.refresh(row)

    # Apply change to the runtime Settings singleton so it takes effect
    # immediately without a restart.
    _apply_to_runtime(key, value)
    logger.info("Setting updated: %s", key)
    return row


def update_settings_bulk(db: Session, updates: dict[str, str]) -> list[str]:
    """Update multiple settings at once. Returns list of updated keys."""
    updated = []
    for key, value in updates.items():
        if key not in ALL_EDITABLE_KEYS:
            continue
        update_setting(db, key, value)
        updated.append(key)
    return updated


def _apply_to_runtime(key: str, value: str):
    """Hot-apply a setting change to the runtime Settings singleton."""
    if key == "PATRONI_NODES":
        env_settings.PATRONI_NODES = [n.strip() for n in value.split(",") if n.strip()]
    elif key == "PATRONI_AUTH_ENABLED":
        env_settings.PATRONI_AUTH_ENABLED = value.lower() == "true"
    elif key in ("PG_PORT", "EMAIL_SMTP_PORT"):
        try:
            setattr(env_settings, key, int(value))
        except ValueError:
            pass
    elif key in ("BACKUP_RETENTION_DAYS", "BACKUP_RETENTION_COPIES"):
        try:
            setattr(env_settings, key, int(value))
        except ValueError:
            pass
    elif key in ("TELEGRAM_ENABLED", "EMAIL_ENABLED", "EMAIL_USE_TLS"):
        setattr(env_settings, key, value.lower() == "true")
    elif key == "EMAIL_TO":
        env_settings.EMAIL_TO = [e.strip() for e in value.split(",") if e.strip()]
    elif key in (
        "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET",
        "GOOGLE_REDIRECT_URI",
        "MICROSOFT_CLIENT_ID",
        "MICROSOFT_CLIENT_SECRET",
        "MICROSOFT_TENANT_ID",
        "MICROSOFT_REDIRECT_URI",
    ):
        setattr(env_settings, key, value)
        _reload_oauth_provider(key)
    else:
        setattr(env_settings, key, value)


def _reload_oauth_provider(key: str):
    """Re-register OAuth provider when SSO credentials change."""
    try:
        from app.routers.auth import oauth, oauth_config

        if key.startswith("GOOGLE_"):
            oauth_config.environ["GOOGLE_CLIENT_ID"] = env_settings.GOOGLE_CLIENT_ID
            oauth_config.environ["GOOGLE_CLIENT_SECRET"] = (
                env_settings.GOOGLE_CLIENT_SECRET
            )
            if env_settings.GOOGLE_CLIENT_ID and env_settings.GOOGLE_CLIENT_SECRET:
                oauth.register(
                    name="google",
                    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
                    client_kwargs={"scope": "openid email profile"},
                    overwrite=True,
                )
                logger.info("Google OAuth provider reloaded")
        elif key.startswith("MICROSOFT_"):
            oauth_config.environ["MICROSOFT_CLIENT_ID"] = (
                env_settings.MICROSOFT_CLIENT_ID
            )
            oauth_config.environ["MICROSOFT_CLIENT_SECRET"] = (
                env_settings.MICROSOFT_CLIENT_SECRET
            )
            if (
                env_settings.MICROSOFT_CLIENT_ID
                and env_settings.MICROSOFT_CLIENT_SECRET
            ):
                oauth.register(
                    name="microsoft",
                    server_metadata_url=f"https://login.microsoftonline.com/{env_settings.MICROSOFT_TENANT_ID}/v2.0/.well-known/openid-configuration",
                    client_kwargs={"scope": "openid email profile"},
                    overwrite=True,
                )
                logger.info("Microsoft OAuth provider reloaded")
    except Exception as e:
        logger.warning("Failed to reload OAuth provider: %s", e)


def init_settings_from_db(db: Session):
    """On startup, load any DB-stored settings into the runtime singleton."""
    rows = db.query(AppSetting).all()
    for row in rows:
        _apply_to_runtime(row.key, row.value)
    if rows:
        logger.info("Loaded %d settings from database", len(rows))
