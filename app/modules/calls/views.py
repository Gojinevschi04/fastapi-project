from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.modules.calls.exceptions import CallSessionNotFoundError
from app.modules.calls.schema import CallSessionResponse, TranscriptResponse
from app.modules.calls.service import CallService
from app.modules.tasks.exceptions import TaskNotFoundError
from app.modules.users.middleware import get_current_user
from app.modules.users.models import User

router = APIRouter(prefix="/tasks", tags=["calls"])


@router.get("/{task_id}/transcript")
async def get_transcript_view(
    task_id: int,
    call_service: Annotated[CallService, Depends(CallService)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> TranscriptResponse:
    try:
        return await call_service.get_transcript(task_id, current_user.id)
    except TaskNotFoundError as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e)) from e
    except CallSessionNotFoundError as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e)) from e


@router.get("/{task_id}/session")
async def get_call_session_view(
    task_id: int,
    call_service: Annotated[CallService, Depends(CallService)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CallSessionResponse:
    try:
        session = await call_service.get_session_by_task(task_id, current_user.id)
    except TaskNotFoundError as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e)) from e
    except CallSessionNotFoundError as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e)) from e

    return CallSessionResponse(
        id=session.id,
        task_id=session.task_id,
        start_time=session.start_time,
        duration=session.duration,
        recording_uri=session.recording_uri,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


@router.get("/{task_id}/recording")
async def download_recording_view(
    task_id: int,
    call_service: Annotated[CallService, Depends(CallService)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> StreamingResponse:
    """Download the call recording as a WAV audio file."""
    try:
        audio_bytes = await call_service.get_recording_audio(task_id, current_user.id)
    except TaskNotFoundError as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e)) from e
    except CallSessionNotFoundError as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e)) from e

    import io

    return StreamingResponse(
        io.BytesIO(audio_bytes),
        media_type="audio/wav",
        headers={"Content-Disposition": f"attachment; filename=recording_task_{task_id}.wav"},
    )
