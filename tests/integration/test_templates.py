from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient

from app.modules.templates.exceptions import TemplateInUseError, TemplateNameExistsError, TemplateNotFoundError


@pytest.mark.asyncio
async def test_create_template(admin_client: AsyncClient) -> None:
    with patch("app.modules.templates.service.TemplateService.create_template") as mock_create:
        mock_template = MagicMock()
        mock_template.id = 1
        mock_template.name = "Make Appointment"
        mock_template.base_script = "Hello, I'd like to make an appointment."
        mock_template.required_slots = ["preferred_date"]
        mock_template.created_at = "2026-01-01T00:00:00"
        mock_template.updated_at = "2026-01-01T00:00:00"
        mock_create.return_value = mock_template

        response = await admin_client.post(
            "/templates/",
            json={"name": "Make Appointment", "base_script": "Hello", "required_slots": ["preferred_date"]},
        )
        assert response.status_code == 201
        assert response.json()["name"] == "Make Appointment"


@pytest.mark.asyncio
async def test_create_template_duplicate(admin_client: AsyncClient) -> None:
    with patch("app.modules.templates.service.TemplateService.create_template") as mock_create:
        mock_create.side_effect = TemplateNameExistsError("Already exists")
        response = await admin_client.post(
            "/templates/",
            json={"name": "Duplicate", "base_script": "Hello", "required_slots": []},
        )
        assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_templates(authenticated_client: AsyncClient) -> None:
    with patch("app.modules.templates.service.TemplateService.get_templates") as mock_get:
        mock_template = MagicMock()
        mock_template.id = 1
        mock_template.name = "Make Appointment"
        mock_template.base_script = "Hello"
        mock_template.required_slots = []
        mock_template.created_at = "2026-01-01T00:00:00"
        mock_template.updated_at = "2026-01-01T00:00:00"
        mock_get.return_value = [mock_template]

        response = await authenticated_client.get("/templates/")
        assert response.status_code == 200
        assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_get_template(authenticated_client: AsyncClient) -> None:
    with patch("app.modules.templates.service.TemplateService.get_template") as mock_get:
        mock_template = MagicMock()
        mock_template.id = 1
        mock_template.name = "Make Appointment"
        mock_template.base_script = "Hello"
        mock_template.required_slots = []
        mock_template.created_at = "2026-01-01T00:00:00"
        mock_template.updated_at = "2026-01-01T00:00:00"
        mock_get.return_value = mock_template

        response = await authenticated_client.get("/templates/1")
        assert response.status_code == 200
        assert response.json()["id"] == 1


@pytest.mark.asyncio
async def test_get_template_not_found(authenticated_client: AsyncClient) -> None:
    with patch("app.modules.templates.service.TemplateService.get_template") as mock_get:
        mock_get.side_effect = TemplateNotFoundError("Not found")
        response = await authenticated_client.get("/templates/999")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_template(admin_client: AsyncClient) -> None:
    with patch("app.modules.templates.service.TemplateService.update_template") as mock_update:
        mock_template = MagicMock()
        mock_template.id = 1
        mock_template.name = "Updated"
        mock_template.base_script = "Hello updated"
        mock_template.required_slots = []
        mock_template.created_at = "2026-01-01T00:00:00"
        mock_template.updated_at = "2026-01-01T00:00:00"
        mock_update.return_value = mock_template

        response = await admin_client.put("/templates/1", json={"name": "Updated"})
        assert response.status_code == 200
        assert response.json()["name"] == "Updated"


@pytest.mark.asyncio
async def test_delete_template(admin_client: AsyncClient) -> None:
    with patch("app.modules.templates.service.TemplateService.delete_template") as mock_delete:
        mock_delete.return_value = True
        response = await admin_client.delete("/templates/1")
        assert response.status_code == 200
        assert response.json()["message"] == "Template deleted successfully"


@pytest.mark.asyncio
async def test_delete_template_in_use(admin_client: AsyncClient) -> None:
    with patch("app.modules.templates.service.TemplateService.delete_template") as mock_delete:
        mock_delete.side_effect = TemplateInUseError("Template is used by tasks")
        response = await admin_client.delete("/templates/1")
        assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_template_non_admin_forbidden(authenticated_client: AsyncClient) -> None:
    response = await authenticated_client.post(
        "/templates/",
        json={"name": "Test", "base_script": "Hello", "required_slots": []},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_template_non_admin_forbidden(authenticated_client: AsyncClient) -> None:
    response = await authenticated_client.put("/templates/1", json={"name": "Updated"})
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_template_non_admin_forbidden(authenticated_client: AsyncClient) -> None:
    response = await authenticated_client.delete("/templates/1")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_templates_unauthenticated(client: AsyncClient) -> None:
    response = await client.get("/templates/")
    assert response.status_code == 401
