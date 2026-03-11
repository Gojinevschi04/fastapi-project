from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.tasks.models import Task
from app.modules.tasks.repository import TaskRepository
from app.modules.tasks.schema import TaskStatus


@pytest.mark.asyncio
async def test_create(mock_session: MagicMock, mock_task: Task) -> None:
    repo = TaskRepository(session=mock_session)
    result = await repo.create(mock_task)

    mock_session.add.assert_called_once_with(mock_task)
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once_with(mock_task)
    assert result == mock_task


@pytest.mark.asyncio
async def test_get_by_id(mock_session: MagicMock, mock_task: Task) -> None:
    mock_result = MagicMock()
    mock_result.first.return_value = mock_task
    mock_session.exec = AsyncMock(return_value=mock_result)

    repo = TaskRepository(session=mock_session)
    result = await repo.get_by_id(1, user_id=1)

    assert result == mock_task


@pytest.mark.asyncio
async def test_get_by_id_not_found(mock_session: MagicMock) -> None:
    mock_result = MagicMock()
    mock_result.first.return_value = None
    mock_session.exec = AsyncMock(return_value=mock_result)

    repo = TaskRepository(session=mock_session)
    result = await repo.get_by_id(999, user_id=1)

    assert result is None


@pytest.mark.asyncio
async def test_get_all_paginated(mock_session: MagicMock, mock_task: Task) -> None:
    mock_tasks_result = MagicMock()
    mock_tasks_result.all.return_value = [mock_task]
    mock_count_result = MagicMock()
    mock_count_result.one.return_value = 1
    mock_session.exec = AsyncMock(side_effect=[mock_tasks_result, mock_count_result])

    repo = TaskRepository(session=mock_session)
    tasks, total = await repo.get_all_paginated(user_id=1, limit=20, offset=0)

    assert len(tasks) == 1
    assert total == 1


@pytest.mark.asyncio
async def test_get_all_paginated_with_status_filter(mock_session: MagicMock, mock_task: Task) -> None:
    mock_tasks_result = MagicMock()
    mock_tasks_result.all.return_value = [mock_task]
    mock_count_result = MagicMock()
    mock_count_result.one.return_value = 1
    mock_session.exec = AsyncMock(side_effect=[mock_tasks_result, mock_count_result])

    repo = TaskRepository(session=mock_session)
    tasks, total = await repo.get_all_paginated(user_id=1, status=TaskStatus.PENDING)

    assert len(tasks) == 1
    assert total == 1


@pytest.mark.asyncio
async def test_update(mock_session: MagicMock, mock_task: Task) -> None:
    repo = TaskRepository(session=mock_session)
    result = await repo.update(mock_task)

    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once_with(mock_task)
    assert result == mock_task


@pytest.mark.asyncio
async def test_count_by_status(mock_session: MagicMock) -> None:
    mock_result = MagicMock()
    mock_result.all.return_value = [(TaskStatus.PENDING, 3), (TaskStatus.COMPLETED, 5)]
    mock_session.exec = AsyncMock(return_value=mock_result)

    repo = TaskRepository(session=mock_session)
    counts = await repo.count_by_status(user_id=1)

    assert counts[TaskStatus.PENDING] == 3
    assert counts[TaskStatus.COMPLETED] == 5
