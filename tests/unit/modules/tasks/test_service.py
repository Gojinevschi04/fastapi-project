from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.tasks.exceptions import InvalidTaskDataError, TaskNotCancellableError, TaskNotFoundError
from app.modules.tasks.models import Task
from app.modules.tasks.repository import TaskRepository
from app.modules.tasks.schema import TaskCreate, TaskStatus
from app.modules.tasks.service import TaskService
from app.modules.templates.exceptions import TemplateNotFoundError
from app.modules.templates.models import DialogTemplate
from app.modules.templates.repository import TemplateRepository


@pytest.mark.asyncio
async def test_create_task_success(mock_task: Task, mock_template: DialogTemplate) -> None:
    mock_task_repo = MagicMock(spec=TaskRepository)
    mock_task_repo.create = AsyncMock(return_value=mock_task)
    mock_template_repo = MagicMock(spec=TemplateRepository)
    mock_template_repo.get_by_id = AsyncMock(return_value=mock_template)

    service = TaskService(task_repository=mock_task_repo, template_repository=mock_template_repo)
    data = TaskCreate(
        target_phone="+37312345678",
        template_id=1,
        slot_data={"preferred_date": "2026-03-20", "preferred_time": "10:00"},
    )
    result = await service.create_task(data, user_id=1)

    assert result == mock_task
    mock_task_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_create_task_template_not_found() -> None:
    mock_task_repo = MagicMock(spec=TaskRepository)
    mock_template_repo = MagicMock(spec=TemplateRepository)
    mock_template_repo.get_by_id = AsyncMock(return_value=None)

    service = TaskService(task_repository=mock_task_repo, template_repository=mock_template_repo)
    data = TaskCreate(target_phone="+37312345678", template_id=999, slot_data={})

    with pytest.raises(TemplateNotFoundError):
        await service.create_task(data, user_id=1)


@pytest.mark.asyncio
async def test_create_task_missing_slots(mock_template: DialogTemplate) -> None:
    mock_task_repo = MagicMock(spec=TaskRepository)
    mock_template_repo = MagicMock(spec=TemplateRepository)
    mock_template_repo.get_by_id = AsyncMock(return_value=mock_template)

    service = TaskService(task_repository=mock_task_repo, template_repository=mock_template_repo)
    data = TaskCreate(target_phone="+37312345678", template_id=1, slot_data={})

    with pytest.raises(InvalidTaskDataError, match="Missing required slots"):
        await service.create_task(data, user_id=1)


@pytest.mark.asyncio
async def test_get_task_success(mock_task: Task) -> None:
    mock_task_repo = MagicMock(spec=TaskRepository)
    mock_task_repo.get_by_id = AsyncMock(return_value=mock_task)
    mock_template_repo = MagicMock(spec=TemplateRepository)

    service = TaskService(task_repository=mock_task_repo, template_repository=mock_template_repo)
    result = await service.get_task(1, user_id=1)

    assert result == mock_task


@pytest.mark.asyncio
async def test_get_task_not_found() -> None:
    mock_task_repo = MagicMock(spec=TaskRepository)
    mock_task_repo.get_by_id = AsyncMock(return_value=None)
    mock_template_repo = MagicMock(spec=TemplateRepository)

    service = TaskService(task_repository=mock_task_repo, template_repository=mock_template_repo)

    with pytest.raises(TaskNotFoundError):
        await service.get_task(999, user_id=1)


@pytest.mark.asyncio
async def test_cancel_task_success(mock_task: Task) -> None:
    mock_task.status = TaskStatus.PENDING
    mock_task_repo = MagicMock(spec=TaskRepository)
    mock_task_repo.get_by_id = AsyncMock(return_value=mock_task)
    mock_task_repo.update = AsyncMock(return_value=mock_task)
    mock_template_repo = MagicMock(spec=TemplateRepository)

    service = TaskService(task_repository=mock_task_repo, template_repository=mock_template_repo)
    result = await service.cancel_task(1, user_id=1)

    assert result.status == TaskStatus.FAILED
    assert result.error_reason == "Cancelled by user"


@pytest.mark.asyncio
async def test_cancel_task_not_cancellable(mock_task: Task) -> None:
    mock_task.status = TaskStatus.IN_PROGRESS
    mock_task_repo = MagicMock(spec=TaskRepository)
    mock_task_repo.get_by_id = AsyncMock(return_value=mock_task)
    mock_template_repo = MagicMock(spec=TemplateRepository)

    service = TaskService(task_repository=mock_task_repo, template_repository=mock_template_repo)

    with pytest.raises(TaskNotCancellableError):
        await service.cancel_task(1, user_id=1)


@pytest.mark.asyncio
async def test_get_stats() -> None:
    mock_task_repo = MagicMock(spec=TaskRepository)
    mock_task_repo.count_by_status = AsyncMock(
        return_value={TaskStatus.PENDING: 2, TaskStatus.COMPLETED: 5, TaskStatus.FAILED: 1}
    )
    mock_template_repo = MagicMock(spec=TemplateRepository)

    service = TaskService(task_repository=mock_task_repo, template_repository=mock_template_repo)
    stats = await service.get_stats(user_id=1)

    assert stats.total == 8
    assert stats.pending == 2
    assert stats.completed == 5
    assert stats.failed == 1
    assert stats.in_progress == 0


@pytest.mark.asyncio
async def test_create_task_with_scheduled_time(mock_template: DialogTemplate) -> None:
    scheduled_task = Task(
        id=2,
        target_phone="+37312345678",
        status=TaskStatus.SCHEDULED,
        template_id=1,
        user_id=1,
        slot_data={"preferred_date": "2026-03-20", "preferred_time": "10:00"},
        scheduled_time="2026-03-25T10:00:00",
    )
    mock_task_repo = MagicMock(spec=TaskRepository)
    mock_task_repo.create = AsyncMock(return_value=scheduled_task)
    mock_template_repo = MagicMock(spec=TemplateRepository)
    mock_template_repo.get_by_id = AsyncMock(return_value=mock_template)

    service = TaskService(task_repository=mock_task_repo, template_repository=mock_template_repo)
    data = TaskCreate(
        target_phone="+37312345678",
        template_id=1,
        slot_data={"preferred_date": "2026-03-20", "preferred_time": "10:00"},
        scheduled_time="2026-03-25T10:00:00",
    )
    result = await service.create_task(data, user_id=1)

    assert result.status == TaskStatus.SCHEDULED
    assert result.scheduled_time is not None
    created_task = mock_task_repo.create.call_args[0][0]
    assert created_task.status == TaskStatus.SCHEDULED


@pytest.mark.asyncio
async def test_get_tasks_paginated(mock_task: Task) -> None:
    mock_task_repo = MagicMock(spec=TaskRepository)
    mock_task_repo.get_all_paginated = AsyncMock(return_value=([mock_task], 1))
    mock_template_repo = MagicMock(spec=TemplateRepository)

    service = TaskService(task_repository=mock_task_repo, template_repository=mock_template_repo)
    tasks, total = await service.get_tasks(user_id=1, limit=20, offset=0)

    assert len(tasks) == 1
    assert total == 1
    mock_task_repo.get_all_paginated.assert_called_once_with(1, 20, 0, None)


@pytest.mark.asyncio
async def test_get_tasks_with_status_filter(mock_task: Task) -> None:
    mock_task_repo = MagicMock(spec=TaskRepository)
    mock_task_repo.get_all_paginated = AsyncMock(return_value=([mock_task], 1))
    mock_template_repo = MagicMock(spec=TemplateRepository)

    service = TaskService(task_repository=mock_task_repo, template_repository=mock_template_repo)
    tasks, total = await service.get_tasks(user_id=1, limit=10, offset=0, status=TaskStatus.PENDING)

    assert len(tasks) == 1
    mock_task_repo.get_all_paginated.assert_called_once_with(1, 10, 0, TaskStatus.PENDING)


@pytest.mark.asyncio
async def test_get_tasks_empty() -> None:
    mock_task_repo = MagicMock(spec=TaskRepository)
    mock_task_repo.get_all_paginated = AsyncMock(return_value=([], 0))
    mock_template_repo = MagicMock(spec=TemplateRepository)

    service = TaskService(task_repository=mock_task_repo, template_repository=mock_template_repo)
    tasks, total = await service.get_tasks(user_id=1)

    assert len(tasks) == 0
    assert total == 0


@pytest.mark.asyncio
async def test_cancel_scheduled_task(mock_task: Task) -> None:
    mock_task.status = TaskStatus.SCHEDULED
    mock_task_repo = MagicMock(spec=TaskRepository)
    mock_task_repo.get_by_id = AsyncMock(return_value=mock_task)
    mock_task_repo.update = AsyncMock(return_value=mock_task)
    mock_template_repo = MagicMock(spec=TemplateRepository)

    service = TaskService(task_repository=mock_task_repo, template_repository=mock_template_repo)
    result = await service.cancel_task(1, user_id=1)

    assert result.status == TaskStatus.FAILED
    assert result.error_reason == "Cancelled by user"


@pytest.mark.asyncio
async def test_get_stats_empty() -> None:
    mock_task_repo = MagicMock(spec=TaskRepository)
    mock_task_repo.count_by_status = AsyncMock(return_value={})
    mock_template_repo = MagicMock(spec=TemplateRepository)

    service = TaskService(task_repository=mock_task_repo, template_repository=mock_template_repo)
    stats = await service.get_stats(user_id=1)

    assert stats.total == 0
    assert stats.pending == 0
    assert stats.completed == 0
    assert stats.failed == 0
    assert stats.in_progress == 0
    assert stats.scheduled == 0


@pytest.mark.asyncio
async def test_cancel_task_not_found() -> None:
    mock_task_repo = MagicMock(spec=TaskRepository)
    mock_task_repo.get_by_id = AsyncMock(return_value=None)
    mock_template_repo = MagicMock(spec=TemplateRepository)

    service = TaskService(task_repository=mock_task_repo, template_repository=mock_template_repo)

    with pytest.raises(TaskNotFoundError):
        await service.cancel_task(999, user_id=1)


@pytest.mark.asyncio
async def test_cancel_completed_task(mock_task: Task) -> None:
    mock_task.status = TaskStatus.COMPLETED
    mock_task_repo = MagicMock(spec=TaskRepository)
    mock_task_repo.get_by_id = AsyncMock(return_value=mock_task)
    mock_template_repo = MagicMock(spec=TemplateRepository)

    service = TaskService(task_repository=mock_task_repo, template_repository=mock_template_repo)

    with pytest.raises(TaskNotCancellableError):
        await service.cancel_task(1, user_id=1)
