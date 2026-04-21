import asyncio
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.logging import get_logger
from app.core.schema import MessageResponse
from app.core.utils import get_request_language
from app.modules.auth.auth_handler import create_ws_ticket, decode_token
from app.modules.auth.schema import (
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.modules.auth.service import AuthService
from app.modules.notifications.email_service import EmailService
from app.modules.users.middleware import get_current_user
from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.modules.users.schema import UserRole

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=TokenResponse)
async def register(
    request: Request,
    data: RegisterRequest,
    user_repository: Annotated[UserRepository, Depends(UserRepository)],
) -> TokenResponse:
    existing_user = await user_repository.get_by_email(data.email)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User with this email already exists")

    hashed_password = AuthService.hash_password(data.password)
    user = User(email=data.email, role=UserRole.USER, hashed_password=hashed_password, phone_number=data.phone_number)
    created_user = await user_repository.create(user)
    lang = get_request_language(request)
    asyncio.create_task(EmailService().send_welcome(created_user.email, language=lang))
    return AuthService.create_tokens(created_user.id)


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    auth_service: Annotated[AuthService, Depends(AuthService)],
) -> TokenResponse:
    user = await auth_service.authenticate_user(data.email, data.password)
    return AuthService.create_tokens(user.id)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    data: RefreshRequest,
) -> TokenResponse:
    return AuthService.refresh_access_token(data.refresh_token)


@router.post("/reset-password")
async def reset_password(
    request: Request,
    data: PasswordResetRequest,
    user_repository: Annotated[UserRepository, Depends(UserRepository)],
) -> MessageResponse:
    user = await user_repository.get_by_email(data.email)
    if user:
        reset_token = AuthService.create_reset_token(user.id)
        lang = get_request_language(request)
        asyncio.create_task(EmailService().send_password_reset(user.email, reset_token, language=lang))
    return MessageResponse(message="If an account with that email exists, a reset link has been sent")


@router.post("/reset-password/confirm")
async def reset_password_confirm(
    request: Request,
    data: PasswordResetConfirm,
    user_repository: Annotated[UserRepository, Depends(UserRepository)],
) -> MessageResponse:
    try:
        payload = decode_token(data.token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset link")

    if payload.get("type") != "reset":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token type")

    user_id = int(payload["sub"])
    user = await user_repository.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset link")

    token_issued_at = payload.get("iat")
    if token_issued_at is not None and user.password_changed_at is not None:
        password_changed_epoch = int(user.password_changed_at.replace(tzinfo=UTC).timestamp())
        if token_issued_at <= password_changed_epoch:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset link already used. Request a new one.",
            )

    user.hashed_password = AuthService.hash_password(data.new_password)
    user.password_changed_at = datetime.now(UTC).replace(tzinfo=None)
    await user_repository.update(user)

    lang = get_request_language(request)
    asyncio.create_task(EmailService().send_password_changed(user.email, language=lang))
    return MessageResponse(message="Password has been reset successfully")


@router.post("/ws-ticket")
async def create_ws_ticket_view(
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    """Issue a 30-second single-purpose token for WebSocket authentication.

    The FE calls this with its normal Bearer token, then uses the returned
    ticket as the `?token=` parameter on the WS URL. Tickets are too
    short-lived to be useful if leaked via proxy/server logs.
    """
    ticket = create_ws_ticket(current_user.id, current_user.role == UserRole.ADMIN)
    return {"ticket": ticket}
