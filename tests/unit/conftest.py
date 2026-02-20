from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from app.modules.files.models import File
from app.modules.files.schema import FileType
from app.modules.users.models import User
from app.modules.users.schema import UserRole


@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock(spec=AsyncSession)
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = AsyncMock()
    session.exec = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def mock_user() -> User:
    return User(
        id=1,
        email="test@example.com",
        role=UserRole.USER,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def mock_admin_user() -> User:
    return User(
        id=2,
        email="admin@example.com",
        role=UserRole.ADMIN,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def mock_file() -> File:
    return File(
        id=1,
        filename="test-uuid.pdf",
        original_filename="test.pdf",
        file_path="/path/to/test-uuid.pdf",
        file_size=1024,
        file_type=FileType.PDF,
        user_id=1,
        content_hash="abc123",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def mock_docx_file() -> File:
    return File(
        id=2,
        filename="test-uuid.docx",
        original_filename="test.docx",
        file_path="/path/to/test-uuid.docx",
        file_size=2048,
        file_type=FileType.DOCX,
        user_id=1,
        content_hash="def456",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def mock_upload_file() -> MagicMock:
    file = MagicMock()
    file.filename = "test.pdf"
    file.read = AsyncMock(return_value=b"file content")
    return file


@pytest.fixture
def sample_file_content() -> bytes:
    return b"Sample PDF content"
