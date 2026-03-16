from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.admin.service import AdminService
from app.modules.calls.repository import CallSessionRepository
from app.modules.tasks.models import Task
from app.modules.tasks.repository import TaskRepository
from app.modules.tasks.schema import TaskStatus
from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.modules.users.schema import UserRole


def _build_service(
    user_repo: MagicMock | None = None,
    task_repo: MagicMock | None = None,
    call_repo: MagicMock | None = None,
) -> AdminService:
    return AdminService(
        user_repository=user_repo or MagicMock(spec=UserRepository),
        task_repository=task_repo or MagicMock(spec=TaskRepository),
        call_session_repository=call_repo or MagicMock(spec=CallSessionRepository),
    )


# --- get_system_stats ---


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

    service = _build_service(mock_user_repo, mock_task_repo, mock_call_repo)
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

    service = _build_service(mock_user_repo, mock_task_repo, mock_call_repo)
    stats = await service.get_system_stats()

    assert stats.total_users == 0
    assert stats.total_tasks == 0
    assert stats.total_calls == 0
    assert stats.tasks_by_status.total == 0


@pytest.mark.asyncio
async def test_get_system_stats_all_statuses_present() -> None:
    mock_user_repo = MagicMock(spec=UserRepository)
    mock_user_repo.count = AsyncMock(return_value=5)

    mock_task_repo = MagicMock(spec=TaskRepository)
    mock_task_repo.count_total = AsyncMock(return_value=25)
    mock_task_repo.count_by_status_all = AsyncMock(
        return_value={
            TaskStatus.PENDING: 5,
            TaskStatus.SCHEDULED: 3,
            TaskStatus.IN_PROGRESS: 2,
            TaskStatus.COMPLETED: 10,
            TaskStatus.FAILED: 5,
        }
    )

    mock_call_repo = MagicMock(spec=CallSessionRepository)
    mock_call_repo.count_total = AsyncMock(return_value=12)

    service = _build_service(mock_user_repo, mock_task_repo, mock_call_repo)
    stats = await service.get_system_stats()

    assert stats.tasks_by_status.pending == 5
    assert stats.tasks_by_status.scheduled == 3
    assert stats.tasks_by_status.in_progress == 2
    assert stats.tasks_by_status.completed == 10
    assert stats.tasks_by_status.failed == 5


# --- get_all_users ---


@pytest.mark.asyncio
async def test_get_all_users() -> None:
    mock_user_repo = MagicMock(spec=UserRepository)
    mock_users = [MagicMock(spec=User), MagicMock(spec=User)]
    mock_user_repo.get_all_paginated = AsyncMock(return_value=(mock_users, 2))

    service = _build_service(user_repo=mock_user_repo)
    users, total = await service.get_all_users(limit=50, offset=0)

    assert total == 2
    assert len(users) == 2
    mock_user_repo.get_all_paginated.assert_called_once_with(0, 50)


@pytest.mark.asyncio
async def test_get_all_users_empty() -> None:
    mock_user_repo = MagicMock(spec=UserRepository)
    mock_user_repo.get_all_paginated = AsyncMock(return_value=([], 0))

    service = _build_service(user_repo=mock_user_repo)
    users, total = await service.get_all_users()

    assert total == 0
    assert len(users) == 0


@pytest.mark.asyncio
async def test_get_all_users_custom_pagination() -> None:
    mock_user_repo = MagicMock(spec=UserRepository)
    mock_user_repo.get_all_paginated = AsyncMock(return_value=([], 10))

    service = _build_service(user_repo=mock_user_repo)
    users, total = await service.get_all_users(limit=5, offset=5)

    assert total == 10
    mock_user_repo.get_all_paginated.assert_called_once_with(5, 5)


# --- get_all_tasks ---


@pytest.mark.asyncio
async def test_get_all_tasks() -> None:
    mock_task_repo = MagicMock(spec=TaskRepository)
    mock_tasks = [MagicMock(spec=Task)]
    mock_task_repo.get_all_paginated_admin = AsyncMock(return_value=(mock_tasks, 1))

    service = _build_service(task_repo=mock_task_repo)
    tasks, total = await service.get_all_tasks(limit=50, offset=0)

    assert total == 1
    assert len(tasks) == 1
    mock_task_repo.get_all_paginated_admin.assert_called_once_with(50, 0, None)


@pytest.mark.asyncio
async def test_get_all_tasks_with_status_filter() -> None:
    mock_task_repo = MagicMock(spec=TaskRepository)
    mock_task_repo.get_all_paginated_admin = AsyncMock(return_value=([], 0))

    service = _build_service(task_repo=mock_task_repo)
    tasks, total = await service.get_all_tasks(limit=10, offset=0, status=TaskStatus.FAILED)

    assert total == 0
    mock_task_repo.get_all_paginated_admin.assert_called_once_with(10, 0, TaskStatus.FAILED)


@pytest.mark.asyncio
async def test_get_all_tasks_custom_pagination() -> None:
    mock_task_repo = MagicMock(spec=TaskRepository)
    mock_task_repo.get_all_paginated_admin = AsyncMock(return_value=([], 50))

    service = _build_service(task_repo=mock_task_repo)
    tasks, total = await service.get_all_tasks(limit=20, offset=30)

    assert total == 50
    mock_task_repo.get_all_paginated_admin.assert_called_once_with(20, 30, None)


# --- update_user_role ---


@pytest.mark.asyncio
async def test_update_user_role() -> None:
    mock_user_repo = MagicMock(spec=UserRepository)
    mock_user = MagicMock(spec=User)
    mock_user.role = UserRole.ADMIN
    mock_user_repo.update_user_role = AsyncMock(return_value=mock_user)

    service = _build_service(user_repo=mock_user_repo)
    result = await service.update_user_role(1, UserRole.ADMIN)

    assert result is not None
    assert result.role == UserRole.ADMIN
    mock_user_repo.update_user_role.assert_called_once_with(1, UserRole.ADMIN)


@pytest.mark.asyncio
async def test_update_user_role_not_found() -> None:
    mock_user_repo = MagicMock(spec=UserRepository)
    mock_user_repo.update_user_role = AsyncMock(return_value=None)

    service = _build_service(user_repo=mock_user_repo)
    result = await service.update_user_role(999, UserRole.ADMIN)

    assert result is None


@pytest.mark.asyncio
async def test_update_user_role_demote_to_user() -> None:
    mock_user_repo = MagicMock(spec=UserRepository)
    mock_user = MagicMock(spec=User)
    mock_user.role = UserRole.USER
    mock_user_repo.update_user_role = AsyncMock(return_value=mock_user)

    service = _build_service(user_repo=mock_user_repo)
    result = await service.update_user_role(1, UserRole.USER)

    assert result is not None
    assert result.role == UserRole.USER


# --- delete_user ---


@pytest.mark.asyncio
async def test_delete_user(mock_user: User) -> None:
    mock_session = AsyncMock()
    # No tasks for user
    mock_result_empty = MagicMock()
    mock_result_empty.all.return_value = []
    mock_session.exec = AsyncMock(return_value=mock_result_empty)
    mock_session.delete = AsyncMock()
    mock_session.commit = AsyncMock()

    mock_user_repo = MagicMock(spec=UserRepository)
    mock_user_repo.get_by_id = AsyncMock(return_value=mock_user)
    mock_user_repo._session = mock_session

    service = _build_service(user_repo=mock_user_repo)
    result = await service.delete_user(1)

    assert result is True
    mock_session.delete.assert_called_once_with(mock_user)
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_delete_user_not_found() -> None:
    mock_user_repo = MagicMock(spec=UserRepository)
    mock_user_repo.get_by_id = AsyncMock(return_value=None)

    service = _build_service(user_repo=mock_user_repo)
    result = await service.delete_user(999)

    assert result is False
