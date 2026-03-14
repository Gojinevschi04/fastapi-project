from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from app.modules.scheduler.service import get_due_tasks
from app.modules.tasks.models import Task
from app.modules.tasks.schema import TaskStatus


@pytest.mark.asyncio
async def test_get_due_tasks_returns_scheduled() -> None:
    past_time = datetime.now() - timedelta(hours=1)
    mock_task = Task(
        id=1,
        target_phone="+37312345678",
        status=TaskStatus.SCHEDULED,
        template_id=1,
        user_id=1,
        slot_data={},
        scheduled_time=past_time,
    )

    mock_result = MagicMock()
    mock_result.all.return_value = [mock_task]

    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.exec = AsyncMock(return_value=mock_result)

    tasks = await get_due_tasks(mock_session)

    assert len(tasks) == 1
    assert tasks[0].id == 1
    assert tasks[0].status == TaskStatus.SCHEDULED


@pytest.mark.asyncio
async def test_get_due_tasks_empty() -> None:
    mock_result = MagicMock()
    mock_result.all.return_value = []

    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.exec = AsyncMock(return_value=mock_result)

    tasks = await get_due_tasks(mock_session)

    assert len(tasks) == 0
