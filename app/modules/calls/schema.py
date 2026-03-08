from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class Speaker(StrEnum):
    AGENT = "agent"
    INTERLOCUTOR = "interlocutor"


class CallSessionResponse(BaseModel):
    id: int
    task_id: int
    start_time: datetime
    duration: int | None
    recording_uri: str | None
    created_at: datetime
    updated_at: datetime


class LogLineResponse(BaseModel):
    id: int
    session_id: int
    timestamp: datetime
    speaker: Speaker
    text: str
    detected_intent: str | None


class TranscriptResponse(BaseModel):
    session: CallSessionResponse
    lines: list[LogLineResponse]
