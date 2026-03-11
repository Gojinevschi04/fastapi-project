from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.calls.exceptions import CallSessionNotFoundError
from app.modules.calls.models import CallSession, LogLine
from app.modules.calls.repository import CallSessionRepository, LogLineRepository
from app.modules.calls.service import CallService
from app.modules.tasks.exceptions import TaskNotFoundError
from app.modules.tasks.models import Task
from app.modules.tasks.repository import TaskRepository


@pytest.mark.asyncio
async def test_get_transcript_success(
    mock_task: Task,
    mock_call_session: CallSession,
    mock_log_lines: list[LogLine],
) -> None:
    mock_task_repo = MagicMock(spec=TaskRepository)
    mock_task_repo.get_by_id = AsyncMock(return_value=mock_task)
    mock_session_repo = MagicMock(spec=CallSessionRepository)
    mock_session_repo.get_by_task_id = AsyncMock(return_value=mock_call_session)
    mock_log_repo = MagicMock(spec=LogLineRepository)
    mock_log_repo.get_by_session_id = AsyncMock(return_value=mock_log_lines)

    service = CallService(
        call_session_repository=mock_session_repo,
        log_line_repository=mock_log_repo,
        task_repository=mock_task_repo,
    )
    result = await service.get_transcript(task_id=1, user_id=1)

    assert result.session.id == mock_call_session.id
    assert len(result.lines) == 2
    assert result.lines[0].speaker == "agent"
    assert result.lines[1].text == "Sure, when would you like to come in?"


@pytest.mark.asyncio
async def test_get_transcript_task_not_found() -> None:
    mock_task_repo = MagicMock(spec=TaskRepository)
    mock_task_repo.get_by_id = AsyncMock(return_value=None)
    mock_session_repo = MagicMock(spec=CallSessionRepository)
    mock_log_repo = MagicMock(spec=LogLineRepository)

    service = CallService(
        call_session_repository=mock_session_repo,
        log_line_repository=mock_log_repo,
        task_repository=mock_task_repo,
    )

    with pytest.raises(TaskNotFoundError):
        await service.get_transcript(task_id=999, user_id=1)


@pytest.mark.asyncio
async def test_get_transcript_no_session(mock_task: Task) -> None:
    mock_task_repo = MagicMock(spec=TaskRepository)
    mock_task_repo.get_by_id = AsyncMock(return_value=mock_task)
    mock_session_repo = MagicMock(spec=CallSessionRepository)
    mock_session_repo.get_by_task_id = AsyncMock(return_value=None)
    mock_log_repo = MagicMock(spec=LogLineRepository)

    service = CallService(
        call_session_repository=mock_session_repo,
        log_line_repository=mock_log_repo,
        task_repository=mock_task_repo,
    )

    with pytest.raises(CallSessionNotFoundError):
        await service.get_transcript(task_id=1, user_id=1)


@pytest.mark.asyncio
async def test_get_session_by_task_success(mock_task: Task, mock_call_session: CallSession) -> None:
    mock_task_repo = MagicMock(spec=TaskRepository)
    mock_task_repo.get_by_id = AsyncMock(return_value=mock_task)
    mock_session_repo = MagicMock(spec=CallSessionRepository)
    mock_session_repo.get_by_task_id = AsyncMock(return_value=mock_call_session)
    mock_log_repo = MagicMock(spec=LogLineRepository)

    service = CallService(
        call_session_repository=mock_session_repo,
        log_line_repository=mock_log_repo,
        task_repository=mock_task_repo,
    )
    result = await service.get_session_by_task(task_id=1, user_id=1)

    assert result == mock_call_session


@pytest.mark.asyncio
async def test_get_session_by_task_not_found() -> None:
    mock_task_repo = MagicMock(spec=TaskRepository)
    mock_task_repo.get_by_id = AsyncMock(return_value=None)
    mock_session_repo = MagicMock(spec=CallSessionRepository)
    mock_log_repo = MagicMock(spec=LogLineRepository)

    service = CallService(
        call_session_repository=mock_session_repo,
        log_line_repository=mock_log_repo,
        task_repository=mock_task_repo,
    )

    with pytest.raises(TaskNotFoundError):
        await service.get_session_by_task(task_id=999, user_id=1)
