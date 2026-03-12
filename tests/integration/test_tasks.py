from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient

from app.modules.tasks.exceptions import TaskNotCancellableError, TaskNotFoundError
from app.modules.tasks.schema import TaskStatsResponse, TaskStatus
from app.modules.templates.exceptions import TemplateNotFoundError


@pytest.mark.asyncio
async def test_create_task(authenticated_client: AsyncClient) -> None:
    with patch("app.modules.tasks.service.TaskService.create_task") as mock_create:
        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.target_phone = "+37312345678"
        mock_task.status = TaskStatus.PENDING
        mock_task.template_id = 1
        mock_task.slot_data = {"preferred_date": "2026-03-20"}
        mock_task.scheduled_time = None
        mock_task.summary = None
        mock_task.error_reason = None
        mock_task.created_at = "2026-01-01T00:00:00"
        mock_task.updated_at = "2026-01-01T00:00:00"
        mock_create.return_value = mock_task

        response = await authenticated_client.post(
            "/tasks/",
            json={"target_phone": "+37312345678", "template_id": 1, "slot_data": {"preferred_date": "2026-03-20"}},
        )
        assert response.status_code == 201
        assert response.json()["target_phone"] == "+37312345678"
        assert response.json()["status"] == "pending"


@pytest.mark.asyncio
async def test_create_task_template_not_found(authenticated_client: AsyncClient) -> None:
    with patch("app.modules.tasks.service.TaskService.create_task") as mock_create:
        mock_create.side_effect = TemplateNotFoundError("Not found")
        response = await authenticated_client.post(
            "/tasks/",
            json={"target_phone": "+37312345678", "template_id": 999, "slot_data": {}},
        )
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_tasks(authenticated_client: AsyncClient) -> None:
    with patch("app.modules.tasks.service.TaskService.get_tasks") as mock_get:
        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.target_phone = "+37312345678"
        mock_task.status = TaskStatus.PENDING
        mock_task.template_id = 1
        mock_task.slot_data = {}
        mock_task.scheduled_time = None
        mock_task.summary = None
        mock_task.error_reason = None
        mock_task.created_at = "2026-01-01T00:00:00"
        mock_task.updated_at = "2026-01-01T00:00:00"
        mock_get.return_value = ([mock_task], 1)

        response = await authenticated_client.get("/tasks/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1


@pytest.mark.asyncio
async def test_get_tasks_with_status_filter(authenticated_client: AsyncClient) -> None:
    with patch("app.modules.tasks.service.TaskService.get_tasks") as mock_get:
        mock_get.return_value = ([], 0)
        response = await authenticated_client.get("/tasks/?status=completed")
        assert response.status_code == 200
        assert response.json()["total"] == 0


@pytest.mark.asyncio
async def test_get_task_stats(authenticated_client: AsyncClient) -> None:
    with patch("app.modules.tasks.service.TaskService.get_stats") as mock_stats:
        mock_stats.return_value = TaskStatsResponse(total=10, pending=2, completed=5, failed=3)
        response = await authenticated_client.get("/tasks/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 10
        assert data["completed"] == 5


@pytest.mark.asyncio
async def test_get_task(authenticated_client: AsyncClient) -> None:
    with patch("app.modules.tasks.service.TaskService.get_task") as mock_get:
        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.target_phone = "+37312345678"
        mock_task.status = TaskStatus.COMPLETED
        mock_task.template_id = 1
        mock_task.slot_data = {}
        mock_task.scheduled_time = None
        mock_task.summary = "Appointment confirmed for March 20"
        mock_task.error_reason = None
        mock_task.created_at = "2026-01-01T00:00:00"
        mock_task.updated_at = "2026-01-01T00:00:00"
        mock_get.return_value = mock_task

        response = await authenticated_client.get("/tasks/1")
        assert response.status_code == 200
        assert response.json()["summary"] == "Appointment confirmed for March 20"


@pytest.mark.asyncio
async def test_get_task_not_found(authenticated_client: AsyncClient) -> None:
    with patch("app.modules.tasks.service.TaskService.get_task") as mock_get:
        mock_get.side_effect = TaskNotFoundError("Not found")
        response = await authenticated_client.get("/tasks/999")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_cancel_task(authenticated_client: AsyncClient) -> None:
    with patch("app.modules.tasks.service.TaskService.cancel_task") as mock_cancel:
        mock_task = MagicMock()
        mock_task.status = TaskStatus.FAILED
        mock_cancel.return_value = mock_task
        response = await authenticated_client.post("/tasks/1/cancel")
        assert response.status_code == 200
        assert response.json()["message"] == "Task cancelled successfully"


@pytest.mark.asyncio
async def test_cancel_task_not_cancellable(authenticated_client: AsyncClient) -> None:
    with patch("app.modules.tasks.service.TaskService.cancel_task") as mock_cancel:
        mock_cancel.side_effect = TaskNotCancellableError("Cannot cancel")
        response = await authenticated_client.post("/tasks/1/cancel")
        assert response.status_code == 409


@pytest.mark.asyncio
async def test_execute_task(authenticated_client: AsyncClient) -> None:
    with patch("app.integrations.call_manager.CallManager.execute_task") as mock_execute:
        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.target_phone = "+37312345678"
        mock_task.status = TaskStatus.COMPLETED
        mock_task.template_id = 1
        mock_task.slot_data = {}
        mock_task.scheduled_time = None
        mock_task.summary = "Appointment confirmed"
        mock_task.error_reason = None
        mock_task.created_at = "2026-01-01T00:00:00"
        mock_task.updated_at = "2026-01-01T00:00:00"
        mock_execute.return_value = mock_task

        response = await authenticated_client.post("/tasks/1/execute")
        assert response.status_code == 200
        assert response.json()["status"] == "completed"
        assert response.json()["summary"] == "Appointment confirmed"


@pytest.mark.asyncio
async def test_execute_task_not_found(authenticated_client: AsyncClient) -> None:
    with patch("app.integrations.call_manager.CallManager.execute_task") as mock_execute:
        mock_execute.side_effect = ValueError("Task 999 not found")
        response = await authenticated_client.post("/tasks/999/execute")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_tasks_unauthenticated(client: AsyncClient) -> None:
    response = await client.get("/tasks/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_task_unauthenticated(client: AsyncClient) -> None:
    response = await client.post(
        "/tasks/",
        json={"target_phone": "+37312345678", "template_id": 1, "slot_data": {}},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_task_stats_unauthenticated(client: AsyncClient) -> None:
    response = await client.get("/tasks/stats")
    assert response.status_code == 401
