import jwt
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.database import async_session
from app.core.logging import get_logger
from app.core.ws_manager import call_broadcaster
from app.modules.auth.auth_handler import decode_token

logger = get_logger(__name__)

router = APIRouter()

WS_CLOSE_UNAUTHORIZED = 4001
WS_CLOSE_FORBIDDEN = 4003


async def _authenticate_ws(token: str | None) -> tuple[int | None, bool]:
    """Validate JWT token and return (user_id, is_admin), or (None, False) if invalid."""
    if not token:
        return None, False
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            return None, False
        user_id = int(payload["sub"])
        is_admin = payload.get("role") == "admin"
        return user_id, is_admin
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, KeyError, ValueError):
        return None, False


async def _user_may_listen(task_id: int, user_id: int, is_admin: bool) -> bool:
    """Admins may listen to any task; regular users only to their own tasks."""
    if is_admin:
        return True
    from app.modules.tasks.repository import TaskRepository

    async with async_session() as session:
        repo = TaskRepository(session=session)
        task = await repo.get_by_id(task_id, user_id)
        return task is not None


@router.websocket("/ws/calls/{task_id}")
async def call_status_ws(websocket: WebSocket, task_id: int, token: str | None = None) -> None:
    user_id, is_admin = await _authenticate_ws(token)
    if user_id is None:
        await websocket.close(code=WS_CLOSE_UNAUTHORIZED, reason="Unauthorized")
        return

    if not await _user_may_listen(task_id, user_id, is_admin):
        await websocket.close(code=WS_CLOSE_FORBIDDEN, reason="Task not owned by user")
        return

    await call_broadcaster.connect(task_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await call_broadcaster.disconnect(task_id, websocket)
