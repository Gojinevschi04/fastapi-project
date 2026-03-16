from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.calls.exceptions import CallSessionNotFoundError
from app.modules.calls.models import CallSession, LogLine
from app.modules.calls.repository import CallSessionRepository, LogLineRepository
from app.modules.calls.schema import Speaker
from app.modules.calls.service import CallService, _demo_audio_cache
from app.modules.tasks.exceptions import TaskNotFoundError
from app.modules.tasks.models import Task
from app.modules.tasks.repository import TaskRepository


@pytest.fixture(autouse=True)
def _clear_audio_cache() -> None:
    _demo_audio_cache.clear()


def _make_service(
    task_repo: MagicMock | None = None,
    session_repo: MagicMock | None = None,
    log_repo: MagicMock | None = None,
) -> CallService:
    """Helper to build CallService with mock repos."""
    return CallService(
        call_session_repository=session_repo or MagicMock(spec=CallSessionRepository),
        log_line_repository=log_repo or MagicMock(spec=LogLineRepository),
        task_repository=task_repo or MagicMock(spec=TaskRepository),
    )


# ---- get_transcript ----


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

    service = _make_service(mock_task_repo, mock_session_repo, mock_log_repo)
    result = await service.get_transcript(task_id=1, user_id=1)

    assert result.session.id == mock_call_session.id
    assert len(result.lines) == 2
    assert result.lines[0].speaker == "agent"
    assert result.lines[1].text == "Sure, when would you like to come in?"


@pytest.mark.asyncio
async def test_get_transcript_returns_session_metadata(
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

    service = _make_service(mock_task_repo, mock_session_repo, mock_log_repo)
    result = await service.get_transcript(task_id=1, user_id=1)

    assert result.session.task_id == mock_call_session.task_id
    assert result.session.duration == mock_call_session.duration
    assert result.session.recording_uri == mock_call_session.recording_uri


@pytest.mark.asyncio
async def test_get_transcript_empty_log_lines(
    mock_task: Task,
    mock_call_session: CallSession,
) -> None:
    mock_task_repo = MagicMock(spec=TaskRepository)
    mock_task_repo.get_by_id = AsyncMock(return_value=mock_task)
    mock_session_repo = MagicMock(spec=CallSessionRepository)
    mock_session_repo.get_by_task_id = AsyncMock(return_value=mock_call_session)
    mock_log_repo = MagicMock(spec=LogLineRepository)
    mock_log_repo.get_by_session_id = AsyncMock(return_value=[])

    service = _make_service(mock_task_repo, mock_session_repo, mock_log_repo)
    result = await service.get_transcript(task_id=1, user_id=1)

    assert result.session.id == mock_call_session.id
    assert len(result.lines) == 0


@pytest.mark.asyncio
async def test_get_transcript_task_not_found() -> None:
    mock_task_repo = MagicMock(spec=TaskRepository)
    mock_task_repo.get_by_id = AsyncMock(return_value=None)

    service = _make_service(mock_task_repo)

    with pytest.raises(TaskNotFoundError):
        await service.get_transcript(task_id=999, user_id=1)


@pytest.mark.asyncio
async def test_get_transcript_no_session(mock_task: Task) -> None:
    mock_task_repo = MagicMock(spec=TaskRepository)
    mock_task_repo.get_by_id = AsyncMock(return_value=mock_task)
    mock_session_repo = MagicMock(spec=CallSessionRepository)
    mock_session_repo.get_by_task_id = AsyncMock(return_value=None)

    service = _make_service(mock_task_repo, mock_session_repo)

    with pytest.raises(CallSessionNotFoundError):
        await service.get_transcript(task_id=1, user_id=1)


@pytest.mark.asyncio
async def test_get_transcript_as_admin(
    mock_task: Task,
    mock_call_session: CallSession,
    mock_log_lines: list[LogLine],
) -> None:
    mock_task_repo = MagicMock(spec=TaskRepository)
    mock_task_repo.get_by_id_any_user = AsyncMock(return_value=mock_task)
    mock_session_repo = MagicMock(spec=CallSessionRepository)
    mock_session_repo.get_by_task_id = AsyncMock(return_value=mock_call_session)
    mock_log_repo = MagicMock(spec=LogLineRepository)
    mock_log_repo.get_by_session_id = AsyncMock(return_value=mock_log_lines)

    service = _make_service(mock_task_repo, mock_session_repo, mock_log_repo)
    result = await service.get_transcript(task_id=1, user_id=99, is_admin=True)

    mock_task_repo.get_by_id_any_user.assert_called_once_with(1)
    mock_task_repo.get_by_id.assert_not_called()
    assert len(result.lines) == 2


@pytest.mark.asyncio
async def test_get_transcript_admin_task_not_found() -> None:
    mock_task_repo = MagicMock(spec=TaskRepository)
    mock_task_repo.get_by_id_any_user = AsyncMock(return_value=None)

    service = _make_service(mock_task_repo)

    with pytest.raises(TaskNotFoundError):
        await service.get_transcript(task_id=999, user_id=99, is_admin=True)


@pytest.mark.asyncio
async def test_get_transcript_log_line_response_fields(
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

    service = _make_service(mock_task_repo, mock_session_repo, mock_log_repo)
    result = await service.get_transcript(task_id=1, user_id=1)

    line = result.lines[1]
    assert line.id == 2
    assert line.session_id == mock_call_session.id
    assert line.detected_intent == "request_date"


# ---- get_session_by_task ----


@pytest.mark.asyncio
async def test_get_session_by_task_success(mock_task: Task, mock_call_session: CallSession) -> None:
    mock_task_repo = MagicMock(spec=TaskRepository)
    mock_task_repo.get_by_id = AsyncMock(return_value=mock_task)
    mock_session_repo = MagicMock(spec=CallSessionRepository)
    mock_session_repo.get_by_task_id = AsyncMock(return_value=mock_call_session)

    service = _make_service(mock_task_repo, mock_session_repo)
    result = await service.get_session_by_task(task_id=1, user_id=1)

    assert result == mock_call_session


@pytest.mark.asyncio
async def test_get_session_by_task_not_found() -> None:
    mock_task_repo = MagicMock(spec=TaskRepository)
    mock_task_repo.get_by_id = AsyncMock(return_value=None)

    service = _make_service(mock_task_repo)

    with pytest.raises(TaskNotFoundError):
        await service.get_session_by_task(task_id=999, user_id=1)


@pytest.mark.asyncio
async def test_get_session_by_task_no_session(mock_task: Task) -> None:
    mock_task_repo = MagicMock(spec=TaskRepository)
    mock_task_repo.get_by_id = AsyncMock(return_value=mock_task)
    mock_session_repo = MagicMock(spec=CallSessionRepository)
    mock_session_repo.get_by_task_id = AsyncMock(return_value=None)

    service = _make_service(mock_task_repo, mock_session_repo)

    with pytest.raises(CallSessionNotFoundError):
        await service.get_session_by_task(task_id=1, user_id=1)


@pytest.mark.asyncio
async def test_get_session_by_task_as_admin(mock_task: Task, mock_call_session: CallSession) -> None:
    mock_task_repo = MagicMock(spec=TaskRepository)
    mock_task_repo.get_by_id_any_user = AsyncMock(return_value=mock_task)
    mock_session_repo = MagicMock(spec=CallSessionRepository)
    mock_session_repo.get_by_task_id = AsyncMock(return_value=mock_call_session)

    service = _make_service(mock_task_repo, mock_session_repo)
    result = await service.get_session_by_task(task_id=1, user_id=99, is_admin=True)

    mock_task_repo.get_by_id_any_user.assert_called_once_with(1)
    assert result == mock_call_session


@pytest.mark.asyncio
async def test_get_session_by_task_admin_no_session(mock_task: Task) -> None:
    mock_task_repo = MagicMock(spec=TaskRepository)
    mock_task_repo.get_by_id_any_user = AsyncMock(return_value=mock_task)
    mock_session_repo = MagicMock(spec=CallSessionRepository)
    mock_session_repo.get_by_task_id = AsyncMock(return_value=None)

    service = _make_service(mock_task_repo, mock_session_repo)

    with pytest.raises(CallSessionNotFoundError):
        await service.get_session_by_task(task_id=1, user_id=99, is_admin=True)


# ---- get_recording_audio ----


@pytest.mark.asyncio
async def test_get_recording_audio_no_uri(mock_task: Task, mock_call_session: CallSession) -> None:
    mock_call_session.recording_uri = None
    mock_task_repo = MagicMock(spec=TaskRepository)
    mock_task_repo.get_by_id = AsyncMock(return_value=mock_task)
    mock_session_repo = MagicMock(spec=CallSessionRepository)
    mock_session_repo.get_by_task_id = AsyncMock(return_value=mock_call_session)

    service = _make_service(mock_task_repo, mock_session_repo)

    with pytest.raises(ValueError, match="No recording available"):
        await service.get_recording_audio(task_id=1, user_id=1)


@pytest.mark.asyncio
async def test_get_recording_audio_fallback_wav_no_log_lines(
    mock_task: Task, mock_call_session: CallSession
) -> None:
    """When Twilio fails and no log lines exist, should fall back to WAV."""
    mock_call_session.recording_uri = "https://fake-twilio-url.com/recording.wav"
    mock_call_session.duration = 3
    mock_task_repo = MagicMock(spec=TaskRepository)
    mock_task_repo.get_by_id = AsyncMock(return_value=mock_task)
    mock_session_repo = MagicMock(spec=CallSessionRepository)
    mock_session_repo.get_by_task_id = AsyncMock(return_value=mock_call_session)
    mock_log_repo = MagicMock(spec=LogLineRepository)
    mock_log_repo.get_by_session_id = AsyncMock(return_value=[])

    service = _make_service(mock_task_repo, mock_session_repo, mock_log_repo)
    audio_bytes, content_type = await service.get_recording_audio(task_id=1, user_id=1)

    assert isinstance(audio_bytes, bytes)
    assert audio_bytes[:4] == b"RIFF"
    assert content_type == "audio/wav"


@pytest.mark.asyncio
async def test_get_recording_audio_fallback_wav_duration_capped(
    mock_task: Task, mock_call_session: CallSession
) -> None:
    """Duration should be capped at 30 seconds for WAV fallback."""
    mock_call_session.recording_uri = "https://fake-twilio-url.com/recording.wav"
    mock_call_session.duration = 120  # 2 minutes
    mock_task_repo = MagicMock(spec=TaskRepository)
    mock_task_repo.get_by_id = AsyncMock(return_value=mock_task)
    mock_session_repo = MagicMock(spec=CallSessionRepository)
    mock_session_repo.get_by_task_id = AsyncMock(return_value=mock_call_session)
    mock_log_repo = MagicMock(spec=LogLineRepository)
    mock_log_repo.get_by_session_id = AsyncMock(return_value=[])

    service = _make_service(mock_task_repo, mock_session_repo, mock_log_repo)

    with patch("app.core.audio.generate_demo_wav") as mock_wav:
        mock_wav.return_value = b"RIFF" + b"\x00" * 10
        audio_bytes, content_type = await service.get_recording_audio(task_id=1, user_id=1)
        mock_wav.assert_called_once_with(duration_seconds=30)

    assert content_type == "audio/wav"


@pytest.mark.asyncio
async def test_get_recording_audio_fallback_wav_default_duration(
    mock_task: Task, mock_call_session: CallSession
) -> None:
    """When session.duration is None, should default to 5 seconds."""
    mock_call_session.recording_uri = "https://fake-twilio-url.com/recording.wav"
    mock_call_session.duration = None
    mock_task_repo = MagicMock(spec=TaskRepository)
    mock_task_repo.get_by_id = AsyncMock(return_value=mock_task)
    mock_session_repo = MagicMock(spec=CallSessionRepository)
    mock_session_repo.get_by_task_id = AsyncMock(return_value=mock_call_session)
    mock_log_repo = MagicMock(spec=LogLineRepository)
    mock_log_repo.get_by_session_id = AsyncMock(return_value=[])

    service = _make_service(mock_task_repo, mock_session_repo, mock_log_repo)

    with patch("app.core.audio.generate_demo_wav") as mock_wav:
        mock_wav.return_value = b"RIFF" + b"\x00" * 10
        await service.get_recording_audio(task_id=1, user_id=1)
        mock_wav.assert_called_once_with(duration_seconds=5)


@pytest.mark.asyncio
async def test_get_recording_audio_tts_from_transcript(
    mock_task: Task,
    mock_call_session: CallSession,
    mock_log_lines: list[LogLine],
) -> None:
    """When Twilio fails but log lines exist, should generate TTS MP3."""
    mock_call_session.recording_uri = "https://fake-twilio-url.com/recording.wav"
    mock_task_repo = MagicMock(spec=TaskRepository)
    mock_task_repo.get_by_id = AsyncMock(return_value=mock_task)
    mock_session_repo = MagicMock(spec=CallSessionRepository)
    mock_session_repo.get_by_task_id = AsyncMock(return_value=mock_call_session)
    mock_log_repo = MagicMock(spec=LogLineRepository)
    mock_log_repo.get_by_session_id = AsyncMock(return_value=mock_log_lines)

    service = _make_service(mock_task_repo, mock_session_repo, mock_log_repo)

    fake_mp3 = b"\xff\xfb\x90\x00" + b"\x00" * 100
    with patch(
        "app.core.audio.generate_demo_conversation_mp3_async",
        new_callable=AsyncMock,
        return_value=fake_mp3,
    ):
        audio_bytes, content_type = await service.get_recording_audio(task_id=1, user_id=1)

    assert audio_bytes == fake_mp3
    assert content_type == "audio/mpeg"


@pytest.mark.asyncio
async def test_get_recording_audio_tts_passes_correct_speaker_labels(
    mock_task: Task,
    mock_call_session: CallSession,
) -> None:
    """Agent lines should be labelled 'Agent', interlocutor lines 'Caller'."""
    mock_call_session.recording_uri = "https://fake-twilio-url.com/recording.wav"
    now = datetime.now()
    log_lines = [
        LogLine(id=1, session_id=1, timestamp=now, speaker=Speaker.AGENT, text="Hi"),
        LogLine(id=2, session_id=1, timestamp=now, speaker=Speaker.INTERLOCUTOR, text="Hello"),
        LogLine(id=3, session_id=1, timestamp=now, speaker=Speaker.AGENT, text="Bye"),
    ]
    mock_task_repo = MagicMock(spec=TaskRepository)
    mock_task_repo.get_by_id = AsyncMock(return_value=mock_task)
    mock_session_repo = MagicMock(spec=CallSessionRepository)
    mock_session_repo.get_by_task_id = AsyncMock(return_value=mock_call_session)
    mock_log_repo = MagicMock(spec=LogLineRepository)
    mock_log_repo.get_by_session_id = AsyncMock(return_value=log_lines)

    service = _make_service(mock_task_repo, mock_session_repo, mock_log_repo)

    fake_mp3 = b"\xff\xfb\x90\x00" + b"\x00" * 50
    with patch(
        "app.core.audio.generate_demo_conversation_mp3_async",
        new_callable=AsyncMock,
        return_value=fake_mp3,
    ) as mock_tts:
        await service.get_recording_audio(task_id=1, user_id=1)
        called_lines = mock_tts.call_args[0][0]

    assert called_lines == [("Agent", "Hi"), ("Caller", "Hello"), ("Agent", "Bye")]


@pytest.mark.asyncio
async def test_get_recording_audio_tts_fallback_when_returns_wav(
    mock_task: Task,
    mock_call_session: CallSession,
    mock_log_lines: list[LogLine],
) -> None:
    """If TTS returns WAV (fallback), should still return WAV content type."""
    mock_call_session.recording_uri = "https://fake-twilio-url.com/recording.wav"
    mock_call_session.duration = 5
    mock_task_repo = MagicMock(spec=TaskRepository)
    mock_task_repo.get_by_id = AsyncMock(return_value=mock_task)
    mock_session_repo = MagicMock(spec=CallSessionRepository)
    mock_session_repo.get_by_task_id = AsyncMock(return_value=mock_call_session)
    mock_log_repo = MagicMock(spec=LogLineRepository)
    mock_log_repo.get_by_session_id = AsyncMock(return_value=mock_log_lines)

    service = _make_service(mock_task_repo, mock_session_repo, mock_log_repo)

    wav_bytes = b"RIFF" + b"\x00" * 100
    with patch(
        "app.core.audio.generate_demo_conversation_mp3_async",
        new_callable=AsyncMock,
        return_value=wav_bytes,
    ):
        audio_bytes, content_type = await service.get_recording_audio(task_id=1, user_id=1)

    # TTS returned WAV (fallback), so service falls through to generate_demo_wav
    assert content_type == "audio/wav"


@pytest.mark.asyncio
async def test_get_recording_audio_as_admin(
    mock_task: Task, mock_call_session: CallSession
) -> None:
    mock_call_session.recording_uri = "https://fake-twilio-url.com/recording.wav"
    mock_call_session.duration = 2
    mock_task_repo = MagicMock(spec=TaskRepository)
    mock_task_repo.get_by_id_any_user = AsyncMock(return_value=mock_task)
    mock_session_repo = MagicMock(spec=CallSessionRepository)
    mock_session_repo.get_by_task_id = AsyncMock(return_value=mock_call_session)
    mock_log_repo = MagicMock(spec=LogLineRepository)
    mock_log_repo.get_by_session_id = AsyncMock(return_value=[])

    service = _make_service(mock_task_repo, mock_session_repo, mock_log_repo)
    audio_bytes, content_type = await service.get_recording_audio(task_id=1, user_id=99, is_admin=True)

    mock_task_repo.get_by_id_any_user.assert_called_once_with(1)
    assert isinstance(audio_bytes, bytes)


@pytest.mark.asyncio
async def test_get_recording_audio_task_not_found() -> None:
    mock_task_repo = MagicMock(spec=TaskRepository)
    mock_task_repo.get_by_id = AsyncMock(return_value=None)

    service = _make_service(mock_task_repo)

    with pytest.raises(TaskNotFoundError):
        await service.get_recording_audio(task_id=999, user_id=1)


@pytest.mark.asyncio
async def test_get_recording_audio_no_call_session(mock_task: Task) -> None:
    mock_task_repo = MagicMock(spec=TaskRepository)
    mock_task_repo.get_by_id = AsyncMock(return_value=mock_task)
    mock_session_repo = MagicMock(spec=CallSessionRepository)
    mock_session_repo.get_by_task_id = AsyncMock(return_value=None)

    service = _make_service(mock_task_repo, mock_session_repo)

    with pytest.raises(CallSessionNotFoundError):
        await service.get_recording_audio(task_id=1, user_id=1)
