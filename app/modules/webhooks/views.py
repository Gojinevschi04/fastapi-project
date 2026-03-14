from typing import Annotated

from fastapi import APIRouter, Depends, Form, Response

from app.core.logging import get_logger
from app.modules.calls.repository import CallSessionRepository
from app.modules.tasks.repository import TaskRepository
from app.modules.tasks.schema import TaskStatus

logger = get_logger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/calls/{task_id}")
async def twilio_call_callback(
    task_id: int,
    task_repository: Annotated[TaskRepository, Depends(TaskRepository)],
    CallSid: str = Form(default=""),
    CallStatus: str = Form(default=""),
) -> Response:
    """TwiML callback — Twilio requests this when the call connects.

    Returns TwiML XML that tells Twilio to play a greeting and record the call.
    The actual AI conversation is handled by the CallManager.execute_task flow.
    """
    logger.info("Twilio callback for task %d, SID=%s, status=%s", task_id, CallSid, CallStatus)

    twiml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response>"
        "<Say voice=\"Polly.Amy\">Hello, please hold while I connect you with our assistant.</Say>"
        "<Pause length=\"1\"/>"
        "<Record maxLength=\"300\" transcribe=\"true\" "
        f'action="/webhooks/calls/{task_id}/recording" />'
        "</Response>"
    )
    return Response(content=twiml, media_type="application/xml")


@router.post("/calls/{task_id}/status")
async def twilio_status_callback(
    task_id: int,
    task_repository: Annotated[TaskRepository, Depends(TaskRepository)],
    call_session_repository: Annotated[CallSessionRepository, Depends(CallSessionRepository)],
    CallSid: str = Form(default=""),
    CallStatus: str = Form(default=""),
    CallDuration: str = Form(default="0"),
) -> Response:
    """Twilio status callback — receives call state changes.

    Status flow: initiated → ringing → answered → completed
    """
    logger.info(
        "Twilio status update for task %d: SID=%s, status=%s, duration=%s",
        task_id,
        CallSid,
        CallStatus,
        CallDuration,
    )

    if CallStatus == "completed":
        call_session = await call_session_repository.get_by_task_id(task_id)
        if call_session and not call_session.duration:
            call_session.duration = int(CallDuration) if CallDuration else 0
            await call_session_repository.update(call_session)
            logger.info("Updated call session duration for task %d: %ss", task_id, CallDuration)

    elif CallStatus in ("busy", "no-answer", "canceled", "failed"):
        logger.warning("Call failed for task %d with status: %s", task_id, CallStatus)
        # Find any task in IN_PROGRESS that matches and mark it failed
        # (user_id=0 is a workaround since webhooks don't have user context,
        # but task_id is unique so we search directly)
        call_session = await call_session_repository.get_by_task_id(task_id)
        if call_session:
            call_session.duration = 0
            await call_session_repository.update(call_session)

    return Response(content="<Response/>", media_type="application/xml")


@router.post("/calls/{task_id}/recording")
async def twilio_recording_callback(
    task_id: int,
    call_session_repository: Annotated[CallSessionRepository, Depends(CallSessionRepository)],
    RecordingUrl: str = Form(default=""),
    RecordingDuration: str = Form(default="0"),
) -> Response:
    """Twilio recording callback — receives the recording URL after recording completes."""
    logger.info(
        "Twilio recording for task %d: url=%s, duration=%s",
        task_id,
        RecordingUrl,
        RecordingDuration,
    )

    if RecordingUrl:
        call_session = await call_session_repository.get_by_task_id(task_id)
        if call_session:
            call_session.recording_uri = RecordingUrl
            await call_session_repository.update(call_session)
            logger.info("Saved recording URL for task %d", task_id)

    return Response(content="<Response/>", media_type="application/xml")
