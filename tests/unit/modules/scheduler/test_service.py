from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from app.modules.scheduler.service import get_due_tasks, transition_task
from app.modules.tasks.models import Task
from app.modules.tasks.schema import TaskStatus


@pytest.mark.asyncio
async def test_get_due_tasks_returns_scheduled() -> None:
    mock_result = MagicMock()
    mock_result.all.return_value = [(1, 10)]  # (task_id, user_id)

    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.exec = AsyncMock(return_value=mock_result)

    tasks = await get_due_tasks(mock_session)

    assert len(tasks) == 1
    assert tasks[0] == (1, 10)


@pytest.mark.asyncio
async def test_get_due_tasks_empty() -> None:
    mock_result = MagicMock()
    mock_result.all.return_value = []

    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.exec = AsyncMock(return_value=mock_result)

    tasks = await get_due_tasks(mock_session)

    assert len(tasks) == 0


@pytest.mark.asyncio
async def test_transition_task_scheduled_to_pending() -> None:
    task = Task(
        id=1,
        target_phone="+37312345678",
        status=TaskStatus.SCHEDULED,
        template_id=1,
        user_id=1,
        slot_data={},
        scheduled_time=datetime.now() - timedelta(hours=1),
    )

    mock_result = MagicMock()
    mock_result.first.return_value = task

    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.exec = AsyncMock(return_value=mock_result)
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()

    await transition_task(mock_session, 1)

    assert task.status == TaskStatus.PENDING
    mock_session.add.assert_called_once_with(task)
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_transition_task_not_found() -> None:
    mock_result = MagicMock()
    mock_result.first.return_value = None

    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.exec = AsyncMock(return_value=mock_result)
    mock_session.commit = AsyncMock()

    await transition_task(mock_session, 999)

    # Should not commit if task not found
    mock_session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_transition_task_already_pending() -> None:
    task = Task(
        id=1,
        target_phone="+37312345678",
        status=TaskStatus.PENDING,
        template_id=1,
        user_id=1,
        slot_data={},
    )

    mock_result = MagicMock()
    mock_result.first.return_value = task

    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.exec = AsyncMock(return_value=mock_result)
    mock_session.commit = AsyncMock()

    await transition_task(mock_session, 1)

    # Should not transition if already PENDING
    assert task.status == TaskStatus.PENDING
    mock_session.commit.assert_not_called()
