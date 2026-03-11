"""Tests for job schedule endpoints."""


def test_list_schedules(client, auth_headers, seeded_schedules):
    resp = client.get("/api/jobs/schedules", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 4


def test_update_schedule_invalid_cron(client, auth_headers, seeded_schedules):
    schedules = client.get("/api/jobs/schedules", headers=auth_headers).json()
    schedule_id = schedules[0]["id"]
    resp = client.put(
        f"/api/jobs/schedules/{schedule_id}",
        json={"cron_expression": "not-a-cron"},
        headers=auth_headers,
    )
    assert resp.status_code in (400, 422)


def test_update_schedule_toggle(client, auth_headers, seeded_schedules):
    schedules = client.get("/api/jobs/schedules", headers=auth_headers).json()
    schedule = schedules[0]
    resp = client.put(
        f"/api/jobs/schedules/{schedule['id']}",
        json={"is_enabled": False},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json() == {"status": "updated"}


def test_update_schedule_not_found(client, auth_headers):
    resp = client.put(
        "/api/jobs/schedules/99999", json={"is_enabled": False}, headers=auth_headers
    )
    assert resp.status_code == 404
