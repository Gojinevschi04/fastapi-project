from pathlib import Path
from typing import Annotated

import aiofiles
from fastapi import Depends

from app.core.constants import WAV_HEADER
from app.core.logging import get_logger
from app.modules.calls.exceptions import CallSessionNotFoundError
from app.modules.calls.models import CallSession
from app.modules.calls.repository import CallSessionRepository, LogLineRepository
from app.modules.calls.schema import (
    CallSessionResponse,
    LogLineResponse,
    TranscriptResponse,
)
from app.modules.tasks.exceptions import TaskNotFoundError
from app.modules.tasks.repository import TaskRepository

logger = get_logger(__name__)

# TODO: production — replace with Redis or an LRU cache with TTL. Module-level dict
# is acceptable for MVP but will leak memory under sustained load and is not shared
# across multiple workers.
_demo_audio_cache: dict[int, tuple[bytes, str]] = {}

CONTENT_TYPE_MP3 = "audio/mpeg"
CONTENT_TYPE_WAV = "audio/wav"


class CallService:
    def __init__(
        self,
        call_session_repository: Annotated[CallSessionRepository, Depends(CallSessionRepository)],
        log_line_repository: Annotated[LogLineRepository, Depends(LogLineRepository)],
        task_repository: Annotated[TaskRepository, Depends(TaskRepository)],
    ) -> None:
        self.call_session_repository = call_session_repository
        self.log_line_repository = log_line_repository
        self.task_repository = task_repository

    async def get_transcript(self, task_id: int, user_id: int, is_admin: bool = False) -> TranscriptResponse:
        if is_admin:
            task = await self.task_repository.get_by_id_any_user(task_id)
        else:
            task = await self.task_repository.get_by_id(task_id, user_id)
        if not task:
            raise TaskNotFoundError(f"Task with id {task_id} not found")

        call_session = await self.call_session_repository.get_by_task_id(task_id)
        if not call_session:
            raise CallSessionNotFoundError(f"No call session found for task {task_id}")

        log_lines = await self.log_line_repository.get_by_session_id(call_session.id)

        return TranscriptResponse(
            session=CallSessionResponse(
                id=call_session.id,
                task_id=call_session.task_id,
                start_time=call_session.start_time,
                duration=call_session.duration,
                recording_uri=call_session.recording_uri,
                created_at=call_session.created_at,
                updated_at=call_session.updated_at,
            ),
            lines=[
                LogLineResponse(
                    id=line.id,
                    session_id=line.session_id,
                    timestamp=line.timestamp,
                    speaker=line.speaker,
                    text=line.text,
                    detected_intent=line.detected_intent,
                )
                for line in log_lines
            ],
        )

    async def get_session_by_task(self, task_id: int, user_id: int, is_admin: bool = False) -> CallSession:
        if is_admin:
            task = await self.task_repository.get_by_id_any_user(task_id)
        else:
            task = await self.task_repository.get_by_id(task_id, user_id)
        if not task:
            raise TaskNotFoundError(f"Task with id {task_id} not found")

        call_session = await self.call_session_repository.get_by_task_id(task_id)
        if not call_session:
            raise CallSessionNotFoundError(f"No call session found for task {task_id}")

        return call_session

    async def get_recording_audio(self, task_id: int, user_id: int, is_admin: bool = False) -> tuple[bytes, str]:
        """Return (audio_bytes, content_type) for the call recording."""
        session = await self.get_session_by_task(task_id, user_id, is_admin=is_admin)
        if not session.recording_uri:
            raise ValueError(f"No recording available for task {task_id}")

        local_result = await self._read_local_recording(session, task_id)
        if local_result:
            return local_result

        twilio_result = await self._fetch_from_twilio(session, task_id)
        if twilio_result:
            return twilio_result

        return await self._generate_demo_audio(session, task_id)

    async def _read_local_recording(self, session: CallSession, task_id: int) -> tuple[bytes, str] | None:
        if not session.local_recording_path:
            return None

        local_path = Path(session.local_recording_path)
        if not local_path.exists():
            return None

        async with aiofiles.open(local_path, "rb") as file:
            audio = await file.read()
        content_type = CONTENT_TYPE_MP3 if local_path.suffix == ".mp3" else CONTENT_TYPE_WAV
        logger.debug("Serving local recording for task %d", task_id)
        return audio, content_type

    async def _fetch_from_twilio(self, session: CallSession, task_id: int) -> tuple[bytes, str] | None:
        try:
            from app.integrations.twilio_adapter import TwilioAdapter

            adapter = TwilioAdapter()
            recording_url = session.recording_uri.replace(".wav", ".mp3")
            audio = await adapter.get_recording_audio(recording_url)
            content_type = CONTENT_TYPE_MP3 if recording_url.endswith(".mp3") else CONTENT_TYPE_WAV
            return audio, content_type
        except Exception:
            logger.warning(
                "Could not fetch recording from Twilio for task %d, generating demo audio from transcript",
                task_id,
            )
            return None

    async def _generate_demo_audio(self, session: CallSession, task_id: int) -> tuple[bytes, str]:
        if task_id in _demo_audio_cache:
            logger.debug("Serving cached demo audio for task %d", task_id)
            return _demo_audio_cache[task_id]

        from app.core.audio import generate_demo_conversation_mp3_async, generate_demo_wav

        log_lines = await self.log_line_repository.get_by_session_id(session.id)
        if log_lines:
            speaker_lines = [("Agent" if line.speaker.value == "agent" else "Caller", line.text) for line in log_lines]
            logger.info("Generating TTS for task %d with %d lines", task_id, len(speaker_lines))
            try:
                audio = await generate_demo_conversation_mp3_async(speaker_lines)
            except Exception:
                logger.exception("TTS generation failed for task %d", task_id)
                audio = b""

            if audio and not audio[:4].startswith(WAV_HEADER):
                logger.info("TTS succeeded for task %d: %d bytes MP3", task_id, len(audio))
                _demo_audio_cache[task_id] = (audio, CONTENT_TYPE_MP3)
                return audio, CONTENT_TYPE_MP3
            else:
                logger.warning(
                    "TTS returned WAV fallback for task %d (%d bytes, header=%s)",
                    task_id,
                    len(audio) if audio else 0,
                    audio[:4].hex() if audio else "empty",
                )

        duration = session.duration or 5
        result = generate_demo_wav(duration_seconds=min(duration, 30)), CONTENT_TYPE_WAV
        _demo_audio_cache[task_id] = result
        return result
