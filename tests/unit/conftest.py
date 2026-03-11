from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from app.modules.calls.models import CallSession, LogLine
from app.modules.calls.schema import Speaker
from app.modules.files.models import File
from app.modules.files.schema import FileType
from app.modules.tasks.models import Task
from app.modules.tasks.schema import TaskStatus
from app.modules.templates.models import DialogTemplate
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


@pytest.fixture
def mock_template() -> DialogTemplate:
    return DialogTemplate(
        id=1,
        name="Make Appointment",
        base_script="Hello, I'd like to make an appointment.",
        required_slots=["preferred_date", "preferred_time"],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def mock_task(mock_template: DialogTemplate) -> Task:
    return Task(
        id=1,
        target_phone="+37312345678",
        status=TaskStatus.PENDING,
        template_id=mock_template.id,
        user_id=1,
        slot_data={"preferred_date": "2026-03-20", "preferred_time": "10:00"},
        scheduled_time=None,
        summary=None,
        error_reason=None,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def mock_call_session(mock_task: Task) -> CallSession:
    return CallSession(
        id=1,
        task_id=mock_task.id,
        start_time=datetime.now(),
        duration=120,
        recording_uri="https://storage.example.com/recordings/1.wav",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def mock_log_lines(mock_call_session: CallSession) -> list[LogLine]:
    now = datetime.now()
    return [
        LogLine(
            id=1,
            session_id=mock_call_session.id,
            timestamp=now,
            speaker=Speaker.AGENT,
            text="Hello, I'd like to make an appointment.",
            detected_intent=None,
            created_at=now,
            updated_at=now,
        ),
        LogLine(
            id=2,
            session_id=mock_call_session.id,
            timestamp=now,
            speaker=Speaker.INTERLOCUTOR,
            text="Sure, when would you like to come in?",
            detected_intent="request_date",
            created_at=now,
            updated_at=now,
        ),
    ]
