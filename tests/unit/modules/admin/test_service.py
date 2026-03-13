from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.admin.service import AdminService
from app.modules.calls.repository import CallSessionRepository
from app.modules.tasks.repository import TaskRepository
from app.modules.tasks.schema import TaskStatus
from app.modules.users.repository import UserRepository


@pytest.mark.asyncio
async def test_get_system_stats() -> None:
    mock_user_repo = MagicMock(spec=UserRepository)
    mock_user_repo.count = AsyncMock(return_value=15)

    mock_task_repo = MagicMock(spec=TaskRepository)
    mock_task_repo.count_total = AsyncMock(return_value=100)
    mock_task_repo.count_by_status_all = AsyncMock(
        return_value={
            TaskStatus.PENDING: 10,
            TaskStatus.COMPLETED: 70,
            TaskStatus.FAILED: 15,
            TaskStatus.IN_PROGRESS: 5,
        }
    )

    mock_call_repo = MagicMock(spec=CallSessionRepository)
    mock_call_repo.count_total = AsyncMock(return_value=85)

    service = AdminService(
        user_repository=mock_user_repo,
        task_repository=mock_task_repo,
        call_session_repository=mock_call_repo,
    )
    stats = await service.get_system_stats()

    assert stats.total_users == 15
    assert stats.total_tasks == 100
    assert stats.total_calls == 85
    assert stats.tasks_by_status.completed == 70
    assert stats.tasks_by_status.failed == 15
    assert stats.tasks_by_status.pending == 10
    assert stats.tasks_by_status.scheduled == 0


@pytest.mark.asyncio
async def test_get_system_stats_empty() -> None:
    mock_user_repo = MagicMock(spec=UserRepository)
    mock_user_repo.count = AsyncMock(return_value=0)

    mock_task_repo = MagicMock(spec=TaskRepository)
    mock_task_repo.count_total = AsyncMock(return_value=0)
    mock_task_repo.count_by_status_all = AsyncMock(return_value={})

    mock_call_repo = MagicMock(spec=CallSessionRepository)
    mock_call_repo.count_total = AsyncMock(return_value=0)

    service = AdminService(
        user_repository=mock_user_repo,
        task_repository=mock_task_repo,
        call_session_repository=mock_call_repo,
    )
    stats = await service.get_system_stats()

    assert stats.total_users == 0
    assert stats.total_tasks == 0
    assert stats.total_calls == 0
    assert stats.tasks_by_status.total == 0
