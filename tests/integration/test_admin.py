from unittest.mock import patch

import pytest
from httpx import AsyncClient

from app.modules.tasks.schema import AdminStatsResponse, TaskStatsResponse


@pytest.mark.asyncio
async def test_get_admin_stats(admin_client: AsyncClient) -> None:
    with patch("app.modules.admin.service.AdminService.get_system_stats") as mock_stats:
        mock_stats.return_value = AdminStatsResponse(
            total_users=10,
            total_tasks=50,
            tasks_by_status=TaskStatsResponse(
                total=50, pending=5, scheduled=3, in_progress=2, completed=35, failed=5
            ),
            total_calls=40,
        )
        response = await admin_client.get("/admin/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_users"] == 10
        assert data["total_tasks"] == 50
        assert data["total_calls"] == 40
        assert data["tasks_by_status"]["completed"] == 35


@pytest.mark.asyncio
async def test_get_admin_stats_non_admin(authenticated_client: AsyncClient) -> None:
    response = await authenticated_client.get("/admin/stats")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_admin_stats_unauthenticated(client: AsyncClient) -> None:
    response = await client.get("/admin/stats")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_password_reset(client: AsyncClient) -> None:
    with patch("app.modules.users.repository.UserRepository.get_by_email") as mock_get:
        mock_get.return_value = None
        response = await client.post("/auth/reset-password", json={"email": "test@example.com"})
        assert response.status_code == 200
        assert "reset link" in response.json()["message"].lower()


@pytest.mark.asyncio
async def test_password_reset_existing_email(client: AsyncClient) -> None:
    with patch("app.modules.users.repository.UserRepository.get_by_email") as mock_get:
        mock_get.return_value = True  # user exists
        response = await client.post("/auth/reset-password", json={"email": "existing@example.com"})
        assert response.status_code == 200
        # Same response whether email exists or not (security)
        assert "reset link" in response.json()["message"].lower()


@pytest.mark.asyncio
async def test_create_user_non_admin_forbidden(authenticated_client: AsyncClient) -> None:
    response = await authenticated_client.post(
        "/users/",
        json={"email": "new@example.com", "password": "test123", "role": "user"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_users_non_admin_forbidden(authenticated_client: AsyncClient) -> None:
    response = await authenticated_client.get("/users/")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_user_non_admin_forbidden(authenticated_client: AsyncClient) -> None:
    response = await authenticated_client.delete("/users/1")
    assert response.status_code == 403
