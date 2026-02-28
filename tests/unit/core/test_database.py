from unittest.mock import AsyncMock, patch

import pytest

from app.core.database import get_db_session


@pytest.mark.asyncio
async def test_get_db_session_yields_session() -> None:
    async for session in get_db_session():
        assert session is not None
        break


@pytest.mark.asyncio
async def test_get_db_session_closes_on_exit() -> None:
    session_mock = AsyncMock()
    mock_session_context = AsyncMock()
    mock_session_context.__aenter__ = AsyncMock(return_value=session_mock)
    mock_session_context.__aexit__ = AsyncMock(return_value=None)

    with patch("app.core.database.async_session", return_value=mock_session_context):
        async for _session in get_db_session():
            pass

    session_mock.close.assert_called_once()


@pytest.mark.asyncio
async def test_get_db_session_rollback_on_exception() -> None:
    session_mock = AsyncMock()
    session_mock.rollback = AsyncMock()
    session_mock.close = AsyncMock()

    mock_session_context = AsyncMock()
    mock_session_context.__aenter__ = AsyncMock(return_value=session_mock)
    mock_session_context.__aexit__ = AsyncMock(return_value=None)

    with patch("app.core.database.async_session", return_value=mock_session_context):
        gen = get_db_session()
        try:
            session = await gen.__anext__()
            await gen.athrow(ValueError("Test error"))
        except (StopAsyncIteration, ValueError):
            pass

    session_mock.rollback.assert_called_once()
    session_mock.close.assert_called_once()
