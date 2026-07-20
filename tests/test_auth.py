# IMPORTS
from fastapi.testclient import TestClient


# ─── Helpers ────────────────────────────────────────────────────────────────

def register_user(client: TestClient, name: str = "Rafaello Ferrari", email: str = "rafaello@test.com", password: str = "Strongpass1") -> dict:
    """Helper to register a user and return the response."""
    return client.post("/api/v1/auth/register", json={
        "name": name,
        "email": email,
        "password": password
    })


def login_user(client: TestClient, email: str = "rafaello@test.com", password: str = "Strongpass1") -> dict:
    """Helper to login and return the response."""
    return client.post("/api/v1/auth/login", json={
        "email": email,
        "password": password
    })


def auth_headers(client: TestClient, email: str = "rafaello@test.com", password: str = "Strongpass1") -> dict:
    """Helper to register, login and return auth headers."""
    register_user(client, email=email, password=password)
    login = login_user(client, email=email, password=password)
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


# ─── Smoke Tests ────────────────────────────────────────────────────────────

def test_health_check(client: TestClient) -> None:
    """API is alive and running."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_register_endpoint_exists(client: TestClient) -> None:
    """Register endpoint is reachable."""
    response = register_user(client)
    assert response.status_code != 404


def test_login_endpoint_exists(client: TestClient) -> None:
    """Login endpoint is reachable."""
    response = login_user(client)
    assert response.status_code != 404


# ─── Register ───────────────────────────────────────────────────────────────

def test_register_success(client: TestClient) -> None:
    """User registers successfully with valid data."""
    response = register_user(client)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "rafaello@test.com"
    assert data["name"] == "Rafaello Ferrari"
    assert "id" in data
    assert "hashed_password" not in data
    assert "password" not in data


def test_register_duplicate_email(client: TestClient) -> None:
    """Registration fails if email is already in use."""
    register_user(client)
    response = register_user(client)
    assert response.status_code == 409


def test_register_email_case_insensitive(client: TestClient) -> None:
    """Emails are normalized — uppercase and lowercase treated as the same."""
    register_user(client, email="Rafaello@test.com")
    response = register_user(client, email="rafaello@test.com")
    assert response.status_code == 409


def test_register_email_with_spaces(client: TestClient) -> None:
    """Emails with leading/trailing spaces are trimmed and normalized."""
    response = register_user(client, email="  rafaello@test.com  ")
    assert response.status_code == 201
    assert response.json()["email"] == "rafaello@test.com"


def test_register_weak_password_too_short(client: TestClient) -> None:
    """Registration fails if password is too short."""
    response = register_user(client, password="Sh0rt")
    assert response.status_code == 422


def test_register_weak_password_no_uppercase(client: TestClient) -> None:
    """Registration fails if password has no uppercase letter."""
    response = register_user(client, password="weakpass1")
    assert response.status_code == 422


def test_register_weak_password_no_number(client: TestClient) -> None:
    """Registration fails if password has no number."""
    response = register_user(client, password="Weakpassword")
    assert response.status_code == 422


def test_register_invalid_email_format(client: TestClient) -> None:
    """Registration fails with an invalid email format."""
    response = register_user(client, email="notanemail")
    assert response.status_code == 422


def test_register_missing_fields(client: TestClient) -> None:
    """Registration fails if required fields are missing."""
    response = client.post("/api/v1/auth/register", json={"email": "rafaello@test.com"})
    assert response.status_code == 422


def test_register_name_trimmed(client: TestClient) -> None:
    """Name with leading/trailing spaces is trimmed."""
    response = register_user(client, name="  Rafaello Ferrari  ")
    assert response.status_code == 201
    assert response.json()["name"] == "Rafaello Ferrari"


# ─── Login ──────────────────────────────────────────────────────────────────

def test_login_success(client: TestClient) -> None:
    """User logs in successfully and receives tokens."""
    register_user(client)
    response = login_user(client)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client: TestClient) -> None:
    """Login fails with wrong password."""
    register_user(client)
    response = login_user(client, password="Wrongpass1")
    assert response.status_code == 401


def test_login_nonexistent_user(client: TestClient) -> None:
    """Login fails if user does not exist."""
    response = login_user(client, email="nobody@test.com")
    assert response.status_code == 401


def test_login_email_case_insensitive(client: TestClient) -> None:
    """Login works regardless of email case."""
    register_user(client, email="rafaello@test.com")
    response = login_user(client, email="RAFAELLO@TEST.COM")
    assert response.status_code == 200


def test_login_missing_fields(client: TestClient) -> None:
    """Login fails if required fields are missing."""
    response = client.post("/api/v1/auth/login", json={"email": "rafaello@test.com"})
    assert response.status_code == 422


# ─── Get Me ─────────────────────────────────────────────────────────────────

def test_get_me_success(client: TestClient) -> None:
    """Authenticated user can fetch their own data."""
    headers = auth_headers(client)
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "rafaello@test.com"
    assert "hashed_password" not in data
    assert "password" not in data


def test_get_me_no_token(client: TestClient) -> None:
    """Unauthenticated request to /me returns 401."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_get_me_invalid_token(client: TestClient) -> None:
    """Invalid token returns 401."""
    response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalidtoken"})
    assert response.status_code == 401


# ─── Update Me ──────────────────────────────────────────────────────────────

def test_update_me_name(client: TestClient) -> None:
    """User can update their name."""
    headers = auth_headers(client)
    response = client.patch("/api/v1/auth/me", json={"name": "New Name"}, headers=headers)
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"


def test_update_me_email(client: TestClient) -> None:
    """User can update their email."""
    headers = auth_headers(client)
    response = client.patch("/api/v1/auth/me", json={"email": "newemail@test.com"}, headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == "newemail@test.com"


def test_update_me_password(client: TestClient) -> None:
    """User can update their password and login with the new one."""
    headers = auth_headers(client)
    client.patch("/api/v1/auth/me", json={"password": "Newpass123"}, headers=headers)
    response = login_user(client, password="Newpass123")
    assert response.status_code == 200


def test_update_me_duplicate_email(client: TestClient) -> None:
    """Update fails if new email belongs to another user."""
    register_user(client, email="other@test.com", name="Other User")
    headers = auth_headers(client, email="rafaello@test.com")
    response = client.patch("/api/v1/auth/me", json={"email": "other@test.com"}, headers=headers)
    assert response.status_code == 409


def test_update_me_no_token(client: TestClient) -> None:
    """Unauthenticated update request returns 401."""
    response = client.patch("/api/v1/auth/me", json={"name": "New Name"})
    assert response.status_code == 401


# ─── Deactivate Me ──────────────────────────────────────────────────────────

def test_deactivate_me_success(client: TestClient) -> None:
    """User can deactivate their own account."""
    headers = auth_headers(client)
    response = client.delete("/api/v1/auth/me", headers=headers)
    assert response.status_code == 204


def test_deactivate_me_cannot_login_after(client: TestClient) -> None:
    """Deactivated user cannot login."""
    headers = auth_headers(client)
    client.delete("/api/v1/auth/me", headers=headers)
    response = login_user(client)
    assert response.status_code == 401


def test_deactivate_me_no_token(client: TestClient) -> None:
    """Unauthenticated deactivate request returns 401."""
    response = client.delete("/api/v1/auth/me")
    assert response.status_code == 401


# ─── Refresh Token ──────────────────────────────────────────────────────────

def test_refresh_token_success(client: TestClient) -> None:
    """User gets a new access token using a valid refresh token."""
    register_user(client)
    login = login_user(client)
    refresh_token = login.json()["refresh_token"]
    response = client.post("/api/v1/auth/refresh", headers={"Authorization": f"Bearer {refresh_token}"})
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_refresh_token_with_access_token_fails(client: TestClient) -> None:
    """Using an access token on /refresh should fail."""
    register_user(client)
    login = login_user(client)
    access_token = login.json()["access_token"]
    response = client.post("/api/v1/auth/refresh", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code in [401, 403]


def test_refresh_token_invalid(client: TestClient) -> None:
    """Invalid refresh token returns 401."""
    response = client.post("/api/v1/auth/refresh", headers={"Authorization": "Bearer invalidtoken"})
    assert response.status_code == 401


def test_refresh_token_no_token(client: TestClient) -> None:
    """Missing token on /refresh returns 401."""
    response = client.post("/api/v1/auth/refresh")
    assert response.status_code == 401


# ─── Honeypot ───────────────────────────────────────────────────────────────

def test_honeypot_admin(client: TestClient) -> None:
    """Request to /admin is blocked."""
    response = client.get("/admin")
    assert response.status_code == 404


def test_honeypot_env(client: TestClient) -> None:
    """Request to /.env is blocked."""
    response = client.get("/.env")
    assert response.status_code == 404


def test_honeypot_wp_admin(client: TestClient) -> None:
    """Request to /wp-admin is blocked."""
    response = client.get("/wp-admin")
    assert response.status_code == 404