from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.templates.models import DialogTemplate
from app.modules.templates.repository import TemplateRepository


@pytest.mark.asyncio
async def test_create(mock_session: MagicMock, mock_template: DialogTemplate) -> None:
    repo = TemplateRepository(session=mock_session)
    result = await repo.create(mock_template)

    mock_session.add.assert_called_once_with(mock_template)
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once_with(mock_template)
    assert result == mock_template


@pytest.mark.asyncio
async def test_get_by_id(mock_session: MagicMock, mock_template: DialogTemplate) -> None:
    mock_result = MagicMock()
    mock_result.first.return_value = mock_template
    mock_session.exec = AsyncMock(return_value=mock_result)

    repo = TemplateRepository(session=mock_session)
    result = await repo.get_by_id(1)

    assert result == mock_template


@pytest.mark.asyncio
async def test_get_by_id_not_found(mock_session: MagicMock) -> None:
    mock_result = MagicMock()
    mock_result.first.return_value = None
    mock_session.exec = AsyncMock(return_value=mock_result)

    repo = TemplateRepository(session=mock_session)
    result = await repo.get_by_id(999)

    assert result is None


@pytest.mark.asyncio
async def test_get_by_name(mock_session: MagicMock, mock_template: DialogTemplate) -> None:
    mock_result = MagicMock()
    mock_result.first.return_value = mock_template
    mock_session.exec = AsyncMock(return_value=mock_result)

    repo = TemplateRepository(session=mock_session)
    result = await repo.get_by_name("Make Appointment")

    assert result == mock_template


@pytest.mark.asyncio
async def test_get_all(mock_session: MagicMock, mock_template: DialogTemplate) -> None:
    mock_result = MagicMock()
    mock_result.all.return_value = [mock_template]
    mock_session.exec = AsyncMock(return_value=mock_result)

    repo = TemplateRepository(session=mock_session)
    result = await repo.get_all()

    assert len(result) == 1
    assert result[0] == mock_template


@pytest.mark.asyncio
async def test_update(mock_session: MagicMock, mock_template: DialogTemplate) -> None:
    repo = TemplateRepository(session=mock_session)
    result = await repo.update(mock_template)

    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once_with(mock_template)
    assert result == mock_template


@pytest.mark.asyncio
async def test_delete_success(mock_session: MagicMock, mock_template: DialogTemplate) -> None:
    mock_result = MagicMock()
    mock_result.first.return_value = mock_template
    mock_session.exec = AsyncMock(return_value=mock_result)

    repo = TemplateRepository(session=mock_session)
    result = await repo.delete(1)

    mock_session.delete.assert_called_once_with(mock_template)
    mock_session.commit.assert_called_once()
    assert result is True


@pytest.mark.asyncio
async def test_delete_not_found(mock_session: MagicMock) -> None:
    mock_result = MagicMock()
    mock_result.first.return_value = None
    mock_session.exec = AsyncMock(return_value=mock_result)

    repo = TemplateRepository(session=mock_session)
    result = await repo.delete(999)

    assert result is False
