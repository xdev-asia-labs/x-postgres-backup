"""Shared test fixtures."""

import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Must be set BEFORE importing app modules so config/dotenv picks them up
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["AUTH_ENABLED"] = "true"
os.environ["ALLOW_REGISTRATION"] = "true"
os.environ.setdefault("APP_SECRET_KEY", "test-secret-key")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key")
os.environ.setdefault("SESSION_SECRET_KEY", "test-session-secret")
os.environ.setdefault("DEFAULT_ADMIN_EMAIL", "admin@example.com")
os.environ.setdefault("DEFAULT_ADMIN_PASSWORD", "admin123")

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import JobSchedule  # noqa: E402
from app.services.auth import ensure_default_admin  # noqa: E402
from app.services.settings import init_settings_from_db  # noqa: E402


def _make_engine():
    """Create a fresh shared-memory SQLite engine per test."""
    return create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


@pytest.fixture()
def db():
    """Fresh in-memory DB session for every test."""
    eng = _make_engine()
    Base.metadata.create_all(bind=eng)
    Session = sessionmaker(bind=eng, autoflush=False, autocommit=False)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=eng)


@pytest.fixture()
def client(db):
    """Test client with overridden DB and scheduler mocked out."""

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    ensure_default_admin(db)
    db.commit()
    init_settings_from_db(db)

    with (
        patch("app.main.start_scheduler"),
        patch("app.main.stop_scheduler"),
        patch("app.routers.api.sync_scheduler_from_db"),
    ):
        with TestClient(app, raise_server_exceptions=True) as c:
            yield c

    app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers(client):
    """Bearer token headers for the default admin user."""
    resp = client.post(
        "/auth/login",
        json={
            "email": "admin@example.com",
            "password": "admin123",
        },
    )
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def seeded_schedules(db):
    """Seed default job schedules into the test DB."""
    defaults = [
        {
            "job_name": "basebackup",
            "job_type": "basebackup",
            "cron_expression": "0 2 * * *",
            "is_enabled": True,
        },
        {
            "job_name": "pgdump",
            "job_type": "pgdump",
            "cron_expression": "0 3 * * *",
            "is_enabled": True,
        },
        {
            "job_name": "cleanup",
            "job_type": "cleanup",
            "cron_expression": "0 6 * * *",
            "is_enabled": True,
        },
        {
            "job_name": "verify",
            "job_type": "verify",
            "cron_expression": "0 4 * * *",
            "is_enabled": True,
        },
    ]
    for d in defaults:
        db.add(JobSchedule(**d))
    db.commit()
