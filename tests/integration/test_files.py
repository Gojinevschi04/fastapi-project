from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient

from app.modules.files.schema import FileType


@pytest.mark.asyncio
async def test_upload_file(admin_client: AsyncClient) -> None:
    with patch("app.modules.files.service.FileService.save_file") as mock_save:
        mock_file = MagicMock()
        mock_file.id = 1
        mock_file.original_filename = "test.pdf"
        mock_file.file_size = 1024
        mock_file.file_type = FileType.PDF
        mock_file.created_at = "2024-01-01T00:00:00"
        mock_file.updated_at = "2024-01-01T00:00:00"
        mock_save.return_value = mock_file

        file_content = b"fake pdf content"
        files = {"file": ("test.pdf", BytesIO(file_content), "application/pdf")}
        response = await admin_client.post("/files/upload", files=files)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["original_filename"] == "test.pdf"
        assert data["file_type"] == FileType.PDF


@pytest.mark.asyncio
async def test_upload_file_no_file(admin_client: AsyncClient) -> None:
    response = await admin_client.post("/files/upload")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_files(admin_client: AsyncClient) -> None:
    with patch("app.modules.files.service.FileService.get_files") as mock_get_files:
        mock_get_files.return_value = []

        response = await admin_client.get("/files/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_file(admin_client: AsyncClient) -> None:
    with patch("app.modules.files.service.FileService.get_file") as mock_get_file:
        mock_file = MagicMock()
        mock_file.id = 1
        mock_file.original_filename = "test.pdf"
        mock_file.file_size = 1024
        mock_file.file_type = FileType.PDF
        mock_file.created_at = "2024-01-01T00:00:00"
        mock_file.updated_at = "2024-01-01T00:00:00"
        mock_get_file.return_value = mock_file

        response = await admin_client.get("/files/1")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1


@pytest.mark.asyncio
async def test_get_file_not_found(admin_client: AsyncClient) -> None:
    with patch("app.modules.files.service.FileService.get_file") as mock_get_file:
        mock_get_file.return_value = None

        response = await admin_client.get("/files/99999")
        assert response.status_code == 400


@pytest.mark.asyncio
async def test_download_file(admin_client: AsyncClient) -> None:
    with patch("app.modules.files.service.FileService.get_file_content") as mock_get_content:
        mock_content = MagicMock()
        mock_content.content = b"file content"
        mock_content.original_filename = "test.pdf"
        mock_content.content_type = "application/pdf"
        mock_get_content.return_value = mock_content

        response = await admin_client.get("/files/1/download")
        assert response.status_code == 200
        assert response.headers["content-type"] is not None


@pytest.mark.asyncio
async def test_download_file_not_found(admin_client: AsyncClient) -> None:
    with patch("app.modules.files.service.FileService.get_file_content") as mock_get_content:
        mock_get_content.return_value = None

        response = await admin_client.get("/files/99999/download")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_file(admin_client: AsyncClient) -> None:
    with patch("app.modules.files.service.FileService.delete_file") as mock_delete:
        mock_delete.return_value = True

        response = await admin_client.delete("/files/1")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data


@pytest.mark.asyncio
async def test_delete_file_not_found(admin_client: AsyncClient) -> None:
    with patch("app.modules.files.service.FileService.delete_file") as mock_delete:
        mock_delete.return_value = False

        response = await admin_client.delete("/files/99999")
        assert response.status_code == 400


# --- Unauthenticated access ---


@pytest.mark.asyncio
async def test_upload_file_unauthenticated(client: AsyncClient) -> None:
    response = await client.post("/files/upload")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_files_unauthenticated(client: AsyncClient) -> None:
    response = await client.get("/files/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_download_file_unauthenticated(client: AsyncClient) -> None:
    response = await client.get("/files/1/download")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_delete_file_unauthenticated(client: AsyncClient) -> None:
    response = await client.delete("/files/1")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_upload_file_rejects_oversized(authenticated_client: AsyncClient) -> None:
    """Regression: upload > MAX_UPLOAD_SIZE_BYTES returns 413."""
    from app.core.constants import MAX_UPLOAD_SIZE_BYTES

    oversized = b"x" * (MAX_UPLOAD_SIZE_BYTES + 1)
    response = await authenticated_client.post(
        "/files/upload",
        files={"file": ("big.pdf", oversized, "application/pdf")},
    )
    assert response.status_code == 413


@pytest.mark.asyncio
async def test_upload_file_accepts_at_limit(authenticated_client: AsyncClient) -> None:
    """Boundary: upload exactly at MAX_UPLOAD_SIZE_BYTES is accepted."""
    from unittest.mock import AsyncMock, patch

    from app.core.constants import MAX_UPLOAD_SIZE_BYTES
    from app.modules.files.models import File
    from app.modules.files.schema import FileType

    at_limit = b"x" * MAX_UPLOAD_SIZE_BYTES
    saved_file = File(
        id=1,
        filename="f.pdf",
        original_filename="big.pdf",
        file_path="/tmp/f.pdf",
        file_size=MAX_UPLOAD_SIZE_BYTES,
        file_type=FileType.PDF,
        user_id=1,
        content_hash="h",
    )
    with patch(
        "app.modules.files.service.FileService.save_file",
        new=AsyncMock(return_value=saved_file),
    ):
        response = await authenticated_client.post(
            "/files/upload",
            files={"file": ("big.pdf", at_limit, "application/pdf")},
        )
    assert response.status_code == 200
