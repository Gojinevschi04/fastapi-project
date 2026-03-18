"""Integration tests for the core auth flow: register, login, refresh, reset-password.

These test the actual auth endpoints (not user CRUD which is in test_auth.py).
"""

from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient

# --- Register ---


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient) -> None:
    with patch("app.modules.users.repository.UserRepository.get_by_email") as mock_get, \
         patch("app.modules.users.repository.UserRepository.create") as mock_create:
        mock_get.return_value = None  # no existing user

        mock_user = MagicMock()
        mock_user.id = 10
        mock_create.return_value = mock_user

        response = await client.post("/auth/register", json={
            "email": "newuser@example.com",
            "password": "securepass123",
            "phone_number": "+37312345678",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient) -> None:
    with patch("app.modules.users.repository.UserRepository.get_by_email") as mock_get:
        mock_get.return_value = MagicMock()  # user exists
        response = await client.post("/auth/register", json={
            "email": "existing@example.com",
            "password": "securepass123",
        })
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_register_invalid_email(client: AsyncClient) -> None:
    response = await client.post("/auth/register", json={
        "email": "not-an-email",
        "password": "securepass123",
    })
    assert response.status_code == 422  # validation error


@pytest.mark.asyncio
async def test_register_password_too_short(client: AsyncClient) -> None:
    response = await client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "short",
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_invalid_phone(client: AsyncClient) -> None:
    response = await client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "securepass123",
        "phone_number": "123",
    })
    assert response.status_code == 422


# --- Login ---


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient) -> None:
    with patch("app.modules.auth.service.AuthService.authenticate_user") as mock_auth:
        mock_user = MagicMock()
        mock_user.id = 1
        mock_auth.return_value = mock_user

        response = await client.post("/auth/login", json={
            "email": "user@example.com",
            "password": "correctpassword",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient) -> None:
    with patch("app.modules.auth.service.AuthService.authenticate_user") as mock_auth:
        from fastapi import HTTPException
        mock_auth.side_effect = HTTPException(status_code=401, detail="Invalid credentials")

        response = await client.post("/auth/login", json={
            "email": "user@example.com",
            "password": "wrongpassword",
        })
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_invalid_email_format(client: AsyncClient) -> None:
    response = await client.post("/auth/login", json={
        "email": "bad-email",
        "password": "password123",
    })
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

        response = await client.post("/auth/refresh", json={
            "refresh_token": "valid_refresh_token",
        })
        assert response.status_code == 200
        assert response.json()["access_token"] == "new_access"


@pytest.mark.asyncio
async def test_refresh_invalid_token(client: AsyncClient) -> None:
    with patch("app.modules.auth.service.AuthService.refresh_access_token") as mock_refresh:
        from fastapi import HTTPException
        mock_refresh.side_effect = HTTPException(status_code=401, detail="Invalid refresh token")

        response = await client.post("/auth/refresh", json={
            "refresh_token": "invalid_token",
        })
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
    response = await client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "x" * 129,
    })
    assert response.status_code == 422


# --- Reset Password Confirm ---


@pytest.mark.asyncio
async def test_reset_password_confirm_success(client: AsyncClient) -> None:
    with patch("app.modules.auth.auth_handler.decode_token") as mock_decode, \
         patch("app.modules.users.repository.UserRepository.get_by_id") as mock_get, \
         patch("app.modules.users.repository.UserRepository.update") as mock_update:
        mock_decode.return_value = {"sub": "1", "type": "reset"}
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.email = "user@example.com"
        mock_get.return_value = mock_user
        mock_update.return_value = mock_user

        response = await client.post("/auth/reset-password/confirm", json={
            "token": "valid-reset-token",
            "new_password": "newpassword123",
        })
        assert response.status_code == 200
        assert "reset successfully" in response.json()["message"].lower()


@pytest.mark.asyncio
async def test_reset_password_confirm_invalid_token(client: AsyncClient) -> None:
    with patch("app.modules.auth.auth_handler.decode_token") as mock_decode:
        mock_decode.side_effect = Exception("Invalid token")
        response = await client.post("/auth/reset-password/confirm", json={
            "token": "bad-token",
            "new_password": "newpassword123",
        })
        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_reset_password_confirm_wrong_token_type(client: AsyncClient) -> None:
    with patch("app.modules.auth.auth_handler.decode_token") as mock_decode:
        mock_decode.return_value = {"sub": "1", "type": "access"}  # not "reset"
        response = await client.post("/auth/reset-password/confirm", json={
            "token": "access-token-not-reset",
            "new_password": "newpassword123",
        })
        assert response.status_code == 400
        assert "token type" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_reset_password_confirm_user_not_found(client: AsyncClient) -> None:
    with patch("app.modules.auth.auth_handler.decode_token") as mock_decode, \
         patch("app.modules.users.repository.UserRepository.get_by_id") as mock_get:
        mock_decode.return_value = {"sub": "999", "type": "reset"}
        mock_get.return_value = None

        response = await client.post("/auth/reset-password/confirm", json={
            "token": "valid-reset-token",
            "new_password": "newpassword123",
        })
        assert response.status_code == 400


@pytest.mark.asyncio
async def test_reset_password_confirm_password_too_short(client: AsyncClient) -> None:
    response = await client.post("/auth/reset-password/confirm", json={
        "token": "any-token",
        "new_password": "short",
    })
    assert response.status_code == 422
