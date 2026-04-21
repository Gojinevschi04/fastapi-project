from datetime import UTC, datetime, timedelta

import jwt

from app.core.config import settings


def create_access_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(UTC) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
        "type": "access",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(UTC) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
        "type": "refresh",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_reset_token(user_id: int) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": now + timedelta(hours=1),
        "type": "reset",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_ws_ticket(user_id: int, is_admin: bool) -> str:
    """Short-lived (30 s) single-purpose token for WebSocket handshake.

    Safer than sending the full access token in a WS URL query string because
    its TTL is tight and its type is restricted — even if the URL is logged,
    the ticket expires before it can be abused.
    """
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "role": "admin" if is_admin else "user",
        "iat": int(now.timestamp()),
        "exp": now + timedelta(seconds=30),
        "type": "ws_ticket",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
