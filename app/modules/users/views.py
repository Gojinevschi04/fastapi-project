from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.schema import MessageResponse
from app.modules.users.schema import UserCreate, UserListResponse, UserResponse, UserUpdate
from app.modules.users.service import AuthService

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    auth_service: Annotated[AuthService, Depends(AuthService)],
) -> UserResponse:
    try:
        return await auth_service.create_user(user_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/users", response_model=UserListResponse)
async def get_users(
    auth_service: Annotated[AuthService, Depends(AuthService)],
    skip: int = 0,
    limit: int = 100,
) -> UserListResponse:
    return await auth_service.get_users(skip, limit)


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    auth_service: Annotated[AuthService, Depends(AuthService)],
) -> UserResponse:
    user = await auth_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    auth_service: Annotated[AuthService, Depends(AuthService)],
) -> UserResponse:
    try:
        user = await auth_service.update_user(user_id, user_data)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    auth_service: Annotated[AuthService, Depends(AuthService)],
) -> MessageResponse:
    success = await auth_service.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return MessageResponse(message="User deleted successfully")
