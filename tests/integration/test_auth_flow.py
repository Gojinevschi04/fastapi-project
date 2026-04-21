"""Integration tests for the core auth flow: register, login, refresh, reset-password.

These test the actual auth endpoints (not user CRUD which is in test_auth.py).
"""

from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient

# --- Register ---


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient) -> None:
    with (
        patch("app.modules.users.repository.UserRepository.get_by_email") as mock_get,
        patch("app.modules.users.repository.UserRepository.create") as mock_create,
    ):
        mock_get.return_value = None  # no existing user

        mock_user = MagicMock()
        mock_user.id = 10
        mock_create.return_value = mock_user

        response = await client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "securepass123",
                "phone_number": "+37312345678",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient) -> None:
    with patch("app.modules.users.repository.UserRepository.get_by_email") as mock_get:
        mock_get.return_value = MagicMock()  # user exists
        response = await client.post(
            "/auth/register",
            json={
                "email": "existing@example.com",
                "password": "securepass123",
            },
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_register_invalid_email(client: AsyncClient) -> None:
    response = await client.post(
        "/auth/register",
        json={
            "email": "not-an-email",
            "password": "securepass123",
        },
    )
    assert response.status_code == 422  # validation error


@pytest.mark.asyncio
async def test_register_password_too_short(client: AsyncClient) -> None:
    response = await client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "short",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_invalid_phone(client: AsyncClient) -> None:
    response = await client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "securepass123",
            "phone_number": "123",
        },
    )
    assert response.status_code == 422


# --- Login ---


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient) -> None:
    with patch("app.modules.auth.service.AuthService.authenticate_user") as mock_auth:
        mock_user = MagicMock()
        mock_user.id = 1
        mock_auth.return_value = mock_user

        response = await client.post(
            "/auth/login",
            json={
                "email": "user@example.com",
                "password": "correctpassword",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient) -> None:
    with patch("app.modules.auth.service.AuthService.authenticate_user") as mock_auth:
        from fastapi import HTTPException

        mock_auth.side_effect = HTTPException(status_code=401, detail="Invalid credentials")

        response = await client.post(
            "/auth/login",
            json={
                "email": "user@example.com",
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_invalid_email_format(client: AsyncClient) -> None:
    response = await client.post(
        "/auth/login",
        json={
            "email": "bad-email",
            "password": "password123",
        },
    )
    assert response.status_code == 422


# --- Refresh ---


@pytest.mark.asyncio
async def test_refresh_success(client: AsyncClient) -> None:
    with patch("app.modules.auth.service.AuthService.refresh_access_token") as mock_refresh:
        mock_refresh.return_value = {
            "access_token": "new_access",
            "refresh_token": "new_refresh",
            "token_type": "bearer",
        }

        response = await client.post(
            "/auth/refresh",
            json={
                "refresh_token": "valid_refresh_token",
            },
        )
        assert response.status_code == 200
        assert response.json()["access_token"] == "new_access"


@pytest.mark.asyncio
async def test_refresh_invalid_token(client: AsyncClient) -> None:
    with patch("app.modules.auth.service.AuthService.refresh_access_token") as mock_refresh:
        from fastapi import HTTPException

        mock_refresh.side_effect = HTTPException(status_code=401, detail="Invalid refresh token")

        response = await client.post(
            "/auth/refresh",
            json={
                "refresh_token": "invalid_token",
            },
        )
        assert response.status_code == 401


# --- Reset Password ---


@pytest.mark.asyncio
async def test_reset_password_always_returns_ok(client: AsyncClient) -> None:
    """Reset password should return 200 regardless of whether email exists (security)."""
    with patch("app.modules.users.repository.UserRepository.get_by_email") as mock_get:
        mock_get.return_value = None  # email doesn't exist
        response = await client.post("/auth/reset-password", json={"email": "nobody@example.com"})
        assert response.status_code == 200
        assert "reset link" in response.json()["message"].lower()


@pytest.mark.asyncio
async def test_reset_password_invalid_email(client: AsyncClient) -> None:
    response = await client.post("/auth/reset-password", json={"email": ""})
    assert response.status_code == 422


# --- Extra validation ---


@pytest.mark.asyncio
async def test_register_missing_email(client: AsyncClient) -> None:
    response = await client.post("/auth/register", json={"password": "securepass123"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_missing_password(client: AsyncClient) -> None:
    response = await client.post("/auth/register", json={"email": "test@example.com"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_empty_body(client: AsyncClient) -> None:
    response = await client.post("/auth/register", json={})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_missing_email(client: AsyncClient) -> None:
    response = await client.post("/auth/login", json={"password": "password123"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_missing_password(client: AsyncClient) -> None:
    response = await client.post("/auth/login", json={"email": "user@example.com"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_empty_body(client: AsyncClient) -> None:
    response = await client.post("/auth/login", json={})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_refresh_missing_token(client: AsyncClient) -> None:
    response = await client.post("/auth/refresh", json={})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_reset_password_missing_body(client: AsyncClient) -> None:
    response = await client.post("/auth/reset-password", json={})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_password_too_long(client: AsyncClient) -> None:
    response = await client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "x" * 129,
        },
    )
    assert response.status_code == 422


# --- Reset Password Confirm ---


@pytest.mark.asyncio
async def test_reset_password_confirm_success(client: AsyncClient) -> None:
    with (
        patch("app.modules.auth.views.decode_token") as mock_decode,
        patch("app.modules.users.repository.UserRepository.get_by_id") as mock_get,
        patch("app.modules.users.repository.UserRepository.update") as mock_update,
    ):
        mock_decode.return_value = {"sub": "1", "type": "reset"}
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.email = "user@example.com"
        mock_get.return_value = mock_user
        mock_update.return_value = mock_user

        response = await client.post(
            "/auth/reset-password/confirm",
            json={
                "token": "valid-reset-token",
                "new_password": "newpassword123",
            },
        )
        assert response.status_code == 200
        assert "reset successfully" in response.json()["message"].lower()


@pytest.mark.asyncio
async def test_reset_password_confirm_invalid_token(client: AsyncClient) -> None:
    with patch("app.modules.auth.views.decode_token") as mock_decode:
        mock_decode.side_effect = Exception("Invalid token")
        response = await client.post(
            "/auth/reset-password/confirm",
            json={
                "token": "bad-token",
                "new_password": "newpassword123",
            },
        )
        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_reset_password_confirm_wrong_token_type(client: AsyncClient) -> None:
    with patch("app.modules.auth.views.decode_token") as mock_decode:
        mock_decode.return_value = {"sub": "1", "type": "access"}  # not "reset"
        response = await client.post(
            "/auth/reset-password/confirm",
            json={
                "token": "access-token-not-reset",
                "new_password": "newpassword123",
            },
        )
        assert response.status_code == 400
        assert "token type" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_reset_password_confirm_user_not_found(client: AsyncClient) -> None:
    with (
        patch("app.modules.auth.views.decode_token") as mock_decode,
        patch("app.modules.users.repository.UserRepository.get_by_id") as mock_get,
    ):
        mock_decode.return_value = {"sub": "999", "type": "reset"}
        mock_get.return_value = None

        response = await client.post(
            "/auth/reset-password/confirm",
            json={
                "token": "valid-reset-token",
                "new_password": "newpassword123",
            },
        )
        assert response.status_code == 400


@pytest.mark.asyncio
async def test_reset_password_confirm_password_too_short(client: AsyncClient) -> None:
    response = await client.post(
        "/auth/reset-password/confirm",
        json={
            "token": "any-token",
            "new_password": "short",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_reset_password_confirm_rejects_token_reuse(client: AsyncClient) -> None:
    """Regression: same reset token cannot be used twice (replay attack)."""
    from datetime import UTC, datetime
    from unittest.mock import AsyncMock, patch

    from app.modules.auth.auth_handler import decode_token
    from app.modules.auth.service import AuthService
    from app.modules.users.models import User
    from app.modules.users.schema import UserRole

    user = User(id=1, email="replay@example.com", role=UserRole.USER, hashed_password="hashed")
    reset_token = AuthService.create_reset_token(user.id)
    token_issued_at = decode_token(reset_token)["iat"]

    with (
        patch(
            "app.modules.users.repository.UserRepository.get_by_id",
            new=AsyncMock(return_value=user),
        ),
        patch(
            "app.modules.users.repository.UserRepository.update",
            new=AsyncMock(return_value=user),
        ),
    ):
        response_first = await client.post(
            "/auth/reset-password/confirm",
            json={"token": reset_token, "new_password": "newpassword123"},
        )
        assert response_first.status_code == 200
        assert user.password_changed_at is not None

        # Pin password_changed_at to one second after the token was issued so the
        # replay check deterministically rejects: token_iat <= password_changed_epoch.
        user.password_changed_at = datetime.fromtimestamp(
            token_issued_at + 1,
            tz=UTC,
        ).replace(tzinfo=None)

        response_second = await client.post(
            "/auth/reset-password/confirm",
            json={"token": reset_token, "new_password": "anotherpassword123"},
        )
        assert response_second.status_code == 400
        assert "already used" in response_second.json()["detail"].lower()


@pytest.mark.asyncio
async def test_ws_ticket_requires_auth(client: AsyncClient) -> None:
    response = await client.post("/auth/ws-ticket")
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_ws_ticket_returns_short_lived_token(authenticated_client: AsyncClient) -> None:
    response = await authenticated_client.post("/auth/ws-ticket")
    assert response.status_code == 200
    body = response.json()
    assert "ticket" in body
    assert len(body["ticket"]) > 20  # non-trivial JWT

    from app.modules.auth.auth_handler import decode_token

    payload = decode_token(body["ticket"])
    assert payload["type"] == "ws_ticket"
    assert payload["sub"] == "1"
    # 30-second TTL → exp - iat should be 30
    assert payload["exp"] - payload["iat"] == 30


@pytest.mark.asyncio
async def test_reset_password_confirm_succeeds_when_password_never_changed(
    client: AsyncClient,
) -> None:
    """Regression: a first-time reset (user.password_changed_at is None) must succeed.

    Guards against "reject if password_changed_at is None" bugs that would lock
    out first-time users of the reset flow.
    """
    from unittest.mock import AsyncMock, patch

    from app.modules.auth.service import AuthService
    from app.modules.users.models import User
    from app.modules.users.schema import UserRole

    user = User(
        id=1,
        email="never-reset@example.com",
        role=UserRole.USER,
        hashed_password="hashed",
        password_changed_at=None,
    )
    reset_token = AuthService.create_reset_token(user.id)

    with (
        patch(
            "app.modules.users.repository.UserRepository.get_by_id",
            new=AsyncMock(return_value=user),
        ),
        patch(
            "app.modules.users.repository.UserRepository.update",
            new=AsyncMock(return_value=user),
        ),
    ):
        response = await client.post(
            "/auth/reset-password/confirm",
            json={"token": reset_token, "new_password": "freshpassword123"},
        )
    assert response.status_code == 200
    assert user.password_changed_at is not None


@pytest.mark.asyncio
async def test_reset_password_confirm_allows_new_token_after_prior_reset(
    client: AsyncClient,
) -> None:
    """Regression: a fresh reset token issued AFTER a prior reset still works.

    Guards against off-by-one in the `iat <= password_changed_epoch` check that
    would permanently lock the user out of self-service reset.
    """
    import time
    from datetime import UTC, datetime
    from unittest.mock import AsyncMock, patch

    from app.modules.auth.service import AuthService
    from app.modules.users.models import User
    from app.modules.users.schema import UserRole

    user = User(
        id=1,
        email="second-reset@example.com",
        role=UserRole.USER,
        hashed_password="hashed",
        password_changed_at=datetime.now(UTC).replace(tzinfo=None),
    )
    time.sleep(1.1)
    fresh_token = AuthService.create_reset_token(user.id)

    with (
        patch(
            "app.modules.users.repository.UserRepository.get_by_id",
            new=AsyncMock(return_value=user),
        ),
        patch(
            "app.modules.users.repository.UserRepository.update",
            new=AsyncMock(return_value=user),
        ),
    ):
        response = await client.post(
            "/auth/reset-password/confirm",
            json={"token": fresh_token, "new_password": "brandnewpw123"},
        )
    assert response.status_code == 200
