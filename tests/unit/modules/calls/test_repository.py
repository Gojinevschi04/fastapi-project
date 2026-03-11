from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.calls.models import CallSession, LogLine
from app.modules.calls.repository import CallSessionRepository, LogLineRepository


@pytest.mark.asyncio
async def test_create_session(mock_session: MagicMock, mock_call_session: CallSession) -> None:
    repo = CallSessionRepository(session=mock_session)
    result = await repo.create(mock_call_session)

    mock_session.add.assert_called_once_with(mock_call_session)
    mock_session.commit.assert_called_once()
    assert result == mock_call_session


@pytest.mark.asyncio
async def test_get_by_task_id(mock_session: MagicMock, mock_call_session: CallSession) -> None:
    mock_result = MagicMock()
    mock_result.first.return_value = mock_call_session
    mock_session.exec = AsyncMock(return_value=mock_result)

    repo = CallSessionRepository(session=mock_session)
    result = await repo.get_by_task_id(1)

    assert result == mock_call_session


@pytest.mark.asyncio
async def test_get_by_task_id_not_found(mock_session: MagicMock) -> None:
    mock_result = MagicMock()
    mock_result.first.return_value = None
    mock_session.exec = AsyncMock(return_value=mock_result)

    repo = CallSessionRepository(session=mock_session)
    result = await repo.get_by_task_id(999)

    assert result is None


@pytest.mark.asyncio
async def test_update_session(mock_session: MagicMock, mock_call_session: CallSession) -> None:
    repo = CallSessionRepository(session=mock_session)
    result = await repo.update(mock_call_session)

    mock_session.commit.assert_called_once()
    assert result == mock_call_session


@pytest.mark.asyncio
async def test_create_log_line(mock_session: MagicMock, mock_log_lines: list[LogLine]) -> None:
    repo = LogLineRepository(session=mock_session)
    result = await repo.create(mock_log_lines[0])

    mock_session.add.assert_called_once_with(mock_log_lines[0])
    mock_session.commit.assert_called_once()
    assert result == mock_log_lines[0]


@pytest.mark.asyncio
async def test_get_by_session_id(mock_session: MagicMock, mock_log_lines: list[LogLine]) -> None:
    mock_result = MagicMock()
    mock_result.all.return_value = mock_log_lines
    mock_session.exec = AsyncMock(return_value=mock_result)

    repo = LogLineRepository(session=mock_session)
    result = await repo.get_by_session_id(1)

    assert len(result) == 2
    assert result[0].speaker == "agent"
    assert result[1].speaker == "interlocutor"
