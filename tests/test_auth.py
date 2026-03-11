"""Tests for authentication endpoints."""


def test_login_success(client):
    resp = client.post(
        "/auth/login",
        json={
            "email": "admin@example.com",
            "password": "admin123",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client):
    resp = client.post(
        "/auth/login",
        json={
            "email": "admin@example.com",
            "password": "wrong-password",
        },
    )
    assert resp.status_code == 401


def test_login_unknown_user(client):
    resp = client.post(
        "/auth/login",
        json={
            "email": "nobody@example.com",
            "password": "pass",
        },
    )
    assert resp.status_code == 401


def test_login_invalid_email(client):
    resp = client.post(
        "/auth/login",
        json={
            "email": "not-an-email",
            "password": "pass",
        },
    )
    assert resp.status_code == 422  # Pydantic validation error


def test_get_me(client, auth_headers):
    resp = client.get("/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "admin@example.com"


def test_get_me_unauthenticated(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 401


def test_token_refresh(client):
    # First login
    login = client.post(
        "/auth/login",
        json={
            "email": "admin@example.com",
            "password": "admin123",
        },
    )
    assert login.status_code == 200
    refresh_token = login.json()["refresh_token"]

    # Refresh tokens
    resp = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    new_data = resp.json()
    assert "access_token" in new_data


def test_logout(client, auth_headers):
    resp = client.post("/auth/logout", headers=auth_headers)
    assert resp.status_code == 200


def test_create_user_by_admin(client, auth_headers):
    resp = client.post(
        "/auth/users",
        json={
            "email": "newuser@example.com",
            "password": "securepass123",
            "username": "newuser",
        },
        headers=auth_headers,
    )
    assert resp.status_code in (200, 201)
    assert resp.json()["email"] == "newuser@example.com"


def test_create_user_duplicate_email(client, auth_headers):
    payload = {
        "email": "duplicate@example.com",
        "password": "securepass123",
        "username": "dupuser",
    }
    client.post("/auth/users", json=payload, headers=auth_headers)
    resp = client.post("/auth/users", json=payload, headers=auth_headers)
    assert resp.status_code in (400, 409)
