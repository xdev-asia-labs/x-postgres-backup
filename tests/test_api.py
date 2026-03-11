"""Tests for health check and basic API endpoints."""


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_unauthenticated_routes_require_login(client):
    """Protected endpoints should return 401 without auth."""
    resp = client.get("/api/backups")
    assert resp.status_code == 401


def test_authenticated_backup_list(client, auth_headers):
    resp = client.get("/api/backups", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_authenticated_backup_disk(client, auth_headers):
    resp = client.get("/api/backups/disk", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "basebackups" in data
    assert "pgdumps" in data
    assert "disk_usage" in data


def test_backup_not_found(client, auth_headers):
    resp = client.get("/api/backups/99999", headers=auth_headers)
    assert resp.status_code == 404


def test_run_backup_invalid_type(client, auth_headers):
    resp = client.post(
        "/api/backups/run", json={"backup_type": "invalid"}, headers=auth_headers
    )
    assert resp.status_code == 400
