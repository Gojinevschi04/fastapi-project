from unittest.mock import patch

import pytest
from httpx import AsyncClient

from app.modules.users.schema import UserCreate, UserListResponse, UserResponse, UserRole, UserUpdate


@pytest.mark.asyncio
async def test_create_user(authenticated_client: AsyncClient) -> None:
    with patch("app.modules.users.service.UserService.create_user") as mock_create:
        mock_user_response = UserResponse(
            id=3,
            email="newuser@example.com",
            role=UserRole.USER,
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        )
        mock_create.return_value = mock_user_response

        user_data = UserCreate(email="newuser@example.com", role=UserRole.USER, password="testpass123")
        response = await authenticated_client.post("/users/", json=user_data.model_dump())
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["email"] == "newuser@example.com"


@pytest.mark.asyncio
async def test_get_users(admin_client: AsyncClient) -> None:
    with patch("app.modules.users.service.UserService.get_users") as mock_get_users:
        mock_response = UserListResponse(
            users=[],
            total=0,
            skip=0,
            limit=100,
        )
        mock_get_users.return_value = mock_response

        response = await admin_client.get("/users/")
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total" in data


@pytest.mark.asyncio
async def test_get_user(admin_client: AsyncClient) -> None:
    with patch("app.modules.users.service.UserService.get_user") as mock_get_user:
        mock_user_response = UserResponse(
            id=1,
            email="test@example.com",
            role=UserRole.USER,
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        )
        mock_get_user.return_value = mock_user_response

        response = await admin_client.get("/users/1")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1


@pytest.mark.asyncio
async def test_get_user_not_found(admin_client: AsyncClient) -> None:
    with patch("app.modules.users.service.UserService.get_user") as mock_get_user:
        mock_get_user.return_value = None

        response = await admin_client.get("/users/99999")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_user(admin_client: AsyncClient) -> None:
    with patch("app.modules.users.service.UserService.update_user") as mock_update:
        mock_user_response = UserResponse(
            id=1,
            email="updated@example.com",
            role=UserRole.USER,
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        )
        mock_update.return_value = mock_user_response

        user_data = UserUpdate(email="updated@example.com")
        response = await admin_client.put("/users/1", json=user_data.model_dump(exclude_none=True))
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "updated@example.com"


@pytest.mark.asyncio
async def test_update_user_not_found(admin_client: AsyncClient) -> None:
    with patch("app.modules.users.service.UserService.update_user") as mock_update:
        mock_update.return_value = None

        user_data = UserUpdate(email="updated@example.com")
        response = await admin_client.put("/users/99999", json=user_data.model_dump(exclude_none=True))
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_user(admin_client: AsyncClient) -> None:
    with patch("app.modules.users.service.UserService.delete_user") as mock_delete:
        mock_delete.return_value = True

        response = await admin_client.delete("/users/1")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data


@pytest.mark.asyncio
async def test_delete_user_not_found(admin_client: AsyncClient) -> None:
    with patch("app.modules.users.service.UserService.delete_user") as mock_delete:
        mock_delete.return_value = False

        response = await admin_client.delete("/users/99999")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_profile(authenticated_client: AsyncClient) -> None:
    with patch("app.modules.users.service.UserService.get_profile") as mock_profile:
        mock_profile.return_value = UserResponse(
            id=1,
            email="test@example.com",
            role=UserRole.USER,
            phone_number="+37312345678",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        )
        response = await authenticated_client.get("/users/me")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["phone_number"] == "+37312345678"


@pytest.mark.asyncio
async def test_update_profile(authenticated_client: AsyncClient) -> None:
    with patch("app.modules.users.service.UserService.update_profile") as mock_update:
        mock_update.return_value = UserResponse(
            id=1,
            email="test@example.com",
            role=UserRole.USER,
            phone_number="+37399999999",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        )
        response = await authenticated_client.put("/users/me", json={"phone_number": "+37399999999"})
        assert response.status_code == 200
        assert response.json()["phone_number"] == "+37399999999"


@pytest.mark.asyncio
async def test_change_password(authenticated_client: AsyncClient) -> None:
    with patch("app.modules.users.service.UserService.change_password") as mock_change:
        mock_change.return_value = True
        response = await authenticated_client.post(
            "/users/me/change-password",
            json={"current_password": "oldpass", "new_password": "newpass123"},
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Password changed successfully"


@pytest.mark.asyncio
async def test_change_password_wrong_current(authenticated_client: AsyncClient) -> None:
    with patch("app.modules.users.service.UserService.change_password") as mock_change:
        mock_change.side_effect = ValueError("Current password is incorrect")
        response = await authenticated_client.post(
            "/users/me/change-password",
            json={"current_password": "wrongpass", "new_password": "newpass123"},
        )
        assert response.status_code == 400
