from typing import Annotated

from fastapi import Depends

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

    async def get_recording_audio(self, task_id: int, user_id: int, is_admin: bool = False) -> bytes:
        session = await self.get_session_by_task(task_id, user_id, is_admin=is_admin)
        if not session.recording_uri:
            raise ValueError(f"No recording available for task {task_id}")

        # Try to fetch from Twilio; fallback to demo audio if unavailable
        try:
            from app.integrations.twilio_adapter import TwilioAdapter

            adapter = TwilioAdapter()
            return await adapter.get_recording_audio(session.recording_uri)
        except Exception:
            logger.warning(
                "Could not fetch recording from Twilio for task %d, serving demo audio",
                task_id,
            )
            from app.core.audio import generate_demo_wav

            duration = session.duration or 5
            return generate_demo_wav(duration_seconds=min(duration, 30))
