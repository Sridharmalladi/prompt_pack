"""Unit tests for auth_service — JWT encode/decode and Google token flow."""
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from jose import jwt

from app.config import settings
from app.services import auth_service
from tests.conftest import TEST_USER_ID


def _make_token(user_id: str, expire_delta: timedelta = timedelta(minutes=60)) -> str:
    expire = datetime.now(timezone.utc) + expire_delta
    return jwt.encode(
        {"sub": user_id, "exp": expire},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


# ── decode_jwt ──────────────────────────────────────────────────

def test_decode_jwt_valid_token():
    token = _make_token(TEST_USER_ID)
    user_id = auth_service.decode_jwt(token)
    assert user_id == TEST_USER_ID


def test_decode_jwt_expired_token():
    token = _make_token(TEST_USER_ID, expire_delta=timedelta(seconds=-1))
    with pytest.raises(ValueError, match="Invalid token"):
        auth_service.decode_jwt(token)


def test_decode_jwt_tampered_token():
    token = _make_token(TEST_USER_ID) + "tampered"
    with pytest.raises(ValueError):
        auth_service.decode_jwt(token)


def test_decode_jwt_wrong_secret():
    token = jwt.encode(
        {"sub": TEST_USER_ID, "exp": datetime.now(timezone.utc) + timedelta(minutes=10)},
        "wrong_secret",
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(ValueError):
        auth_service.decode_jwt(token)


# ── google_login ────────────────────────────────────────────────

def test_google_login_returns_token_and_user():
    mock_profile = {
        "google_id": "google-123",
        "email": "test@example.com",
        "name": "Test User",
        "avatar_url": "https://example.com/avatar.jpg",
    }
    mock_user = {
        "id": TEST_USER_ID,
        "email": "test@example.com",
        "name": "Test User",
    }

    with (
        patch("app.services.auth_service.verify_google_token", return_value=mock_profile),
        patch("app.db.crud.upsert_user", return_value=mock_user),
    ):
        result = auth_service.google_login("fake-google-token")

    assert "access_token" in result
    assert result["user"]["email"] == "test@example.com"
    # Verify the token we got back actually decodes correctly
    user_id = auth_service.decode_jwt(result["access_token"])
    assert user_id == TEST_USER_ID


def test_google_login_invalid_token():
    with patch(
        "app.services.auth_service.verify_google_token",
        side_effect=ValueError("Invalid Google token"),
    ):
        with pytest.raises(ValueError, match="Invalid Google token"):
            auth_service.google_login("bad-token")
