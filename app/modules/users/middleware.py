from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.modules.users.schema import UserRole
from app.modules.users.service import UserService


async def get_current_user(
    request: Request,
    user_repository: Annotated[UserRepository, Depends(UserRepository)],
    auth_service: Annotated[UserService, Depends(UserService)],
) -> User:
    sealed_session = request.cookies.get("wos_session")

    if not sealed_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No session cookie provided",
        )

    session = auth_service.load_sealed_session(sealed_session)
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")

    auth_response = session.authenticate()

    if not auth_response.authenticated:
        if auth_response.reason == "no_session_cookie_provided":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No session cookie provided",
            )

        try:
            refresh_result = session.refresh()
            if not refresh_result.authenticated:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired - please refresh",
                headers=(
                    {"X-Session-Refresh": refresh_result.sealed_session}
                    if hasattr(refresh_result, "sealed_session")
                    else {}
                ),
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication failed: {str(e)}",
            )

    if not auth_response.user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found in session")

    workos_user = auth_response.user
    user = await user_repository.get_by_workos_id(workos_user.id)

    if user is None:
        workos_role = await auth_service.get_user_role_from_workos(workos_user.id)
        user = User(
            workos_id=workos_user.id,
            email=workos_user.email if workos_user.email else "",
            role=workos_role,
        )
        user = await user_repository.create(user)

    return user


async def get_current_admin_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return current_user
