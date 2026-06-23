from datetime import datetime, timedelta, timezone

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from jose import JWTError, jwt

from app.config import settings
from app.db import crud


def verify_google_token(token: str) -> dict:
    """
    Verify a Google ID token and return the decoded payload.
    Raises ValueError if the token is invalid or issued for the wrong client.
    """
    try:
        payload = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            settings.google_client_id,
        )
    except Exception as exc:
        raise ValueError(f"Invalid Google token: {exc}") from exc

    return {
        "google_id": payload["sub"],
        "email": payload["email"],
        "name": payload.get("name", ""),
        "avatar_url": payload.get("picture", ""),
    }


def _issue_jwt(user_id: str) -> str:
    """Create a signed JWT for the given user ID."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expiry_minutes)
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def google_login(google_token: str) -> dict:
    """
    Full login flow:
    1. Verify the Google ID token
    2. Upsert the user in the DB (create on first login, update on return)
    3. Issue and return a JWT

    Returns: { "access_token": "...", "user": { "id", "email", "name" } }
    """
    profile = verify_google_token(google_token)

    user = crud.upsert_user(
        google_id=profile["google_id"],
        email=profile["email"],
        name=profile["name"],
        avatar_url=profile["avatar_url"],
    )

    access_token = _issue_jwt(user["id"])

    return {
        "access_token": access_token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
        },
    }


def dev_login(email: str) -> dict:
    """Dev-only: skip Google OAuth, issue a JWT directly. Never call in production."""
    fake_google_id = f"dev-{email}"
    user = crud.upsert_user(
        google_id=fake_google_id,
        email=email,
        name=email.split("@")[0],
        avatar_url="",
    )
    access_token = _issue_jwt(user["id"])
    return {
        "access_token": access_token,
        "user": {"id": user["id"], "email": user["email"], "name": user["name"]},
    }


def decode_jwt(token: str) -> str:
    """
    Decode and validate a JWT, returning the user_id (sub claim).
    Raises ValueError if expired or tampered.
    Used by auth_middleware to protect routes.
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        user_id: str = payload.get("sub")
        if not user_id:
            raise ValueError("Token missing subject claim.")
        return user_id
    except JWTError as exc:
        raise ValueError(f"Invalid token: {exc}") from exc
