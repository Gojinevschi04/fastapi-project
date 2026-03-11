from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.templates.exceptions import TemplateNameExistsError, TemplateNotFoundError
from app.modules.templates.models import DialogTemplate
from app.modules.templates.repository import TemplateRepository
from app.modules.templates.schema import TemplateCreate, TemplateUpdate
from app.modules.templates.service import TemplateService


@pytest.mark.asyncio
async def test_create_template_success(mock_template: DialogTemplate) -> None:
    mock_repo = MagicMock(spec=TemplateRepository)
    mock_repo.get_by_name = AsyncMock(return_value=None)
    mock_repo.create = AsyncMock(return_value=mock_template)

    service = TemplateService(template_repository=mock_repo)
    data = TemplateCreate(name="Make Appointment", base_script="Hello", required_slots=["date"])
    result = await service.create_template(data)

    assert result == mock_template
    mock_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_create_template_duplicate_name(mock_template: DialogTemplate) -> None:
    mock_repo = MagicMock(spec=TemplateRepository)
    mock_repo.get_by_name = AsyncMock(return_value=mock_template)

    service = TemplateService(template_repository=mock_repo)
    data = TemplateCreate(name="Make Appointment", base_script="Hello", required_slots=[])

    with pytest.raises(TemplateNameExistsError):
        await service.create_template(data)


@pytest.mark.asyncio
async def test_get_template_success(mock_template: DialogTemplate) -> None:
    mock_repo = MagicMock(spec=TemplateRepository)
    mock_repo.get_by_id = AsyncMock(return_value=mock_template)

    service = TemplateService(template_repository=mock_repo)
    result = await service.get_template(1)

    assert result == mock_template


@pytest.mark.asyncio
async def test_get_template_not_found() -> None:
    mock_repo = MagicMock(spec=TemplateRepository)
    mock_repo.get_by_id = AsyncMock(return_value=None)

    service = TemplateService(template_repository=mock_repo)

    with pytest.raises(TemplateNotFoundError):
        await service.get_template(999)


@pytest.mark.asyncio
async def test_get_templates(mock_template: DialogTemplate) -> None:
    mock_repo = MagicMock(spec=TemplateRepository)
    mock_repo.get_all = AsyncMock(return_value=[mock_template])

    service = TemplateService(template_repository=mock_repo)
    result = await service.get_templates()

    assert len(result) == 1


@pytest.mark.asyncio
async def test_update_template_success(mock_template: DialogTemplate) -> None:
    mock_repo = MagicMock(spec=TemplateRepository)
    mock_repo.get_by_id = AsyncMock(return_value=mock_template)
    mock_repo.get_by_name = AsyncMock(return_value=None)
    mock_repo.update = AsyncMock(return_value=mock_template)

    service = TemplateService(template_repository=mock_repo)
    data = TemplateUpdate(name="Updated Name")
    result = await service.update_template(1, data)

    assert result == mock_template


@pytest.mark.asyncio
async def test_update_template_not_found() -> None:
    mock_repo = MagicMock(spec=TemplateRepository)
    mock_repo.get_by_id = AsyncMock(return_value=None)

    service = TemplateService(template_repository=mock_repo)
    data = TemplateUpdate(name="Updated")

    with pytest.raises(TemplateNotFoundError):
        await service.update_template(999, data)


@pytest.mark.asyncio
async def test_delete_template_success(mock_template: DialogTemplate) -> None:
    mock_repo = MagicMock(spec=TemplateRepository)
    mock_repo.get_by_id = AsyncMock(return_value=mock_template)
    mock_repo.delete = AsyncMock(return_value=True)

    service = TemplateService(template_repository=mock_repo)
    result = await service.delete_template(1)

    assert result is True


@pytest.mark.asyncio
async def test_delete_template_not_found() -> None:
    mock_repo = MagicMock(spec=TemplateRepository)
    mock_repo.get_by_id = AsyncMock(return_value=None)

    service = TemplateService(template_repository=mock_repo)

    with pytest.raises(TemplateNotFoundError):
        await service.delete_template(999)
