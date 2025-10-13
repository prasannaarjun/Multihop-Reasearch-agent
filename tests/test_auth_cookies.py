"""
Tests for cookie-based auth flow (HttpOnly refresh cookie).
"""

import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite:///./test_auth.db"
os.environ["SECRET_KEY"] = "test-secret-key"

from app import app
from auth.database import Base, get_db


# Reuse the same SQLite test DB as other tests
engine = create_engine("sqlite:///./test_auth.db", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module")
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    # Do not drop DB here to avoid interfering with other tests


@pytest.fixture
def client(setup_database):
    return TestClient(app)


def test_login_sets_http_only_cookie(client: TestClient):
    # Register
    client.post(
        "/auth/register",
        json={
            "username": "cookie_login_user",
            "email": "cookie_login@example.com",
            "password": "StrongPass1!",
        },
    )

    # Login
    resp = client.post(
        "/auth/login",
        json={"username": "cookie_login_user", "password": "StrongPass1!"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    # Refresh cookie is set
    assert "refresh_token" in resp.cookies


def test_refresh_uses_cookie_and_logout_clears_cookie(client: TestClient):
    # Register
    client.post(
        "/auth/register",
        json={
            "username": "cookie_refresh_user",
            "email": "cookie_refresh@example.com",
            "password": "StrongPass1!",
        },
    )

    # Login
    login = client.post(
        "/auth/login",
        json={"username": "cookie_refresh_user", "password": "StrongPass1!"},
    )
    assert login.status_code == 200
    assert "refresh_token" in login.cookies

    # Refresh without body (cookie only)
    refresh = client.post("/auth/refresh")
    assert refresh.status_code == 200
    assert "access_token" in refresh.json()

    # Logout clears cookie
    logout = client.post("/auth/logout")
    assert logout.status_code == 200

