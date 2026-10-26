"""Automated unit and integration tests for AUREX HMS authentication."""

import pytest
from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
from models import User
from auth import hash_password


@pytest.fixture(scope="module")
def setup_test_users():
    """Ensure clean test fixture users exist in the database."""
    db = SessionLocal()
    test_email = "test.patient@example.com"
    inactive_email = "inactive.user@example.com"
    doctor_email = "test.doctor@example.com"

    try:
        # Create or update active test patient
        user = db.query(User).filter(User.email == test_email).first()
        if not user:
            user = User(
                full_name="Test Patient User",
                email=test_email,
                role="patient",
                password_hash=hash_password("ValidPassword123!"),
                is_active=True,
            )
            db.add(user)
        else:
            user.password_hash = hash_password("ValidPassword123!")
            user.is_active = True

        # Create or update inactive test user
        inactive = db.query(User).filter(User.email == inactive_email).first()
        if not inactive:
            inactive = User(
                full_name="Inactive Test User",
                email=inactive_email,
                role="patient",
                password_hash=hash_password("ValidPassword123!"),
                is_active=False,
            )
            db.add(inactive)
        else:
            inactive.password_hash = hash_password("ValidPassword123!")
            inactive.is_active = False

        # Create or update doctor user
        doctor = db.query(User).filter(User.email == doctor_email).first()
        if not doctor:
            doctor = User(
                full_name="Test Doctor User",
                email=doctor_email,
                role="doctor",
                password_hash=hash_password("ValidPassword123!"),
                is_active=True,
            )
            db.add(doctor)
        else:
            doctor.password_hash = hash_password("ValidPassword123!")
            doctor.is_active = True

        db.commit()
    finally:
        db.close()


def test_health_check():
    """Verify health endpoint reports healthy and database connected."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"


def test_health_database_check():
    """Verify dedicated database health endpoint."""
    client = TestClient(app)
    response = client.get("/health/database")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}


def test_login_success(setup_test_users):
    """Verify successful login returns user data and sets session cookies."""
    client = TestClient(app)
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test.patient@example.com",
            "password": "ValidPassword123!",
            "category": "patient",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test.patient@example.com"
    assert data["role"] == "patient"
    assert "token" in data
    assert "csrf_token" in data

    # Verify cookies were set
    cookies = response.cookies
    assert "hms_session" in cookies
    assert "hms_csrf" in cookies


def test_login_supports_login_id_and_role_fields(setup_test_users):
    """Verify login works when using 'login_id' instead of 'email', and 'role' instead of 'category'."""
    client = TestClient(app)
    response = client.post(
        "/api/v1/auth/login",
        json={
            "login_id": "test.patient@example.com",
            "password": "ValidPassword123!",
            "role": "patient",
        },
    )
    assert response.status_code == 200
    assert response.json()["email"] == "test.patient@example.com"


def test_login_wrong_password(setup_test_users):
    """Verify login fails safely with 401 when password is incorrect."""
    client = TestClient(app)
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test.patient@example.com",
            "password": "WrongPassword999!",
            "category": "patient",
        },
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."


def test_login_nonexistent_user():
    """Verify login fails safely with 401 when user does not exist."""
    client = TestClient(app)
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent.user.xyz@example.com",
            "password": "AnyPassword123!",
            "category": "patient",
        },
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."


def test_login_wrong_role(setup_test_users):
    """Verify login fails with 403 when selected category does not match user account."""
    client = TestClient(app)
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test.patient@example.com",
            "password": "ValidPassword123!",
            "category": "doctor",  # Patient attempting to login as Doctor
        },
    )
    assert response.status_code == 403
    assert "does not match your assigned account role" in response.json()["detail"]


def test_login_inactive_user(setup_test_users):
    """Verify login fails with 403 when account is deactivated."""
    client = TestClient(app)
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "inactive.user@example.com",
            "password": "ValidPassword123!",
            "category": "patient",
        },
    )
    assert response.status_code == 403
    assert "inactive" in response.json()["detail"].lower()


def test_login_missing_fields():
    """Verify login fails with 422 when required fields are missing."""
    client = TestClient(app)
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test.patient@example.com"},  # Missing password
    )
    assert response.status_code == 422


def test_auth_me_with_cookie(setup_test_users):
    """Verify /api/v1/auth/me returns profile using session cookie."""
    client = TestClient(app)
    # 1. Login to establish cookie session
    login_res = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test.patient@example.com",
            "password": "ValidPassword123!",
            "category": "patient",
        },
    )
    assert login_res.status_code == 200

    # 2. Call /auth/me with the same client
    me_res = client.get("/api/v1/auth/me")
    assert me_res.status_code == 200
    data = me_res.json()
    assert data["email"] == "test.patient@example.com"
    assert data["role"] == "patient"


def test_auth_me_with_bearer_token(setup_test_users):
    """Verify /api/v1/auth/me also supports Bearer token (Postman / Swagger UI)."""
    client = TestClient(app)
    login_res = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test.patient@example.com",
            "password": "ValidPassword123!",
            "category": "patient",
        },
    )
    assert login_res.status_code == 200
    token = login_res.json()["token"]

    # Use fresh unauthenticated client and pass Bearer token in header
    fresh_client = TestClient(app)
    me_res = fresh_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "test.patient@example.com"


def test_auth_me_unauthenticated():
    """Verify /api/v1/auth/me returns 401 when no session is provided."""
    fresh_client = TestClient(app)
    response = fresh_client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert "Authentication required" in response.json()["detail"]


def test_logout():
    """Verify /api/v1/auth/logout returns success and clears session cookies."""
    client = TestClient(app)
    # Log in first
    client.post(
        "/api/v1/auth/login",
        json={
            "email": "test.patient@example.com",
            "password": "ValidPassword123!",
            "category": "patient",
        },
    )
    # Then logout
    response = client.post("/api/v1/auth/logout")
    assert response.status_code == 200
    assert response.json()["message"] == "Logged out successfully"
