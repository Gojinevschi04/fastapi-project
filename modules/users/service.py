from typing import Annotated

from fastapi import Depends

from core.logging import get_logger
from modules.users.models import User
from modules.users.repository import UserRepository
from modules.users.schema import (
    UserCreate,
    UserListResponse,
    UserResponse,
    UserRole,
    UserUpdate,
)

logger = get_logger(__name__)


class AuthService:
    def __init__(
        self,
        user_repository: Annotated[UserRepository, Depends(UserRepository)],
    ) -> None:
        self.user_repository = user_repository

    async def create_user(self, user_data: UserCreate) -> UserResponse:
        existing_user = await self.user_repository.get_by_email(user_data.email)
        if existing_user:
            raise ValueError("User with this email already exists")

        user = User(email=user_data.email, role=UserRole.USER)
        created_user = await self.user_repository.create(user)
        return UserResponse(
            id=created_user.id,
            email=created_user.email,
            role=created_user.role,
            created_at=created_user.created_at.isoformat(),
            updated_at=created_user.updated_at.isoformat(),
        )

    async def update_user(self, user_id: int, user_data: UserUpdate) -> UserResponse | None:
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            return None

        if user_data.email is not None:
            existing_user = await self.user_repository.get_by_email(user_data.email)
            if existing_user and existing_user.id != user_id:
                raise ValueError("User with this email already exists")
            user.email = user_data.email

        if user_data.role is not None:
            user.role = user_data.role

        updated_user = await self.user_repository.update(user)
        return UserResponse(
            id=updated_user.id,
            email=updated_user.email,
            role=updated_user.role,
            created_at=updated_user.created_at.isoformat(),
            updated_at=updated_user.updated_at.isoformat(),
        )

    async def delete_user(self, user_id: int) -> bool:
        return await self.user_repository.delete(user_id)

    async def get_user(self, user_id: int) -> UserResponse | None:
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            return None

        return UserResponse(
            id=user.id,
            email=user.email,
            role=user.role,
            created_at=user.created_at.isoformat(),
            updated_at=user.updated_at.isoformat(),
        )

    async def get_users(self, skip: int = 0, limit: int = 100) -> UserListResponse:
        users, total = await self.user_repository.get_all_paginated(skip, limit)
        user_responses = [
            UserResponse(
                id=user.id,
                email=user.email,
                role=user.role,
                created_at=user.created_at.isoformat(),
                updated_at=user.updated_at.isoformat(),
            )
            for user in users
        ]
        return UserListResponse(users=user_responses, total=total, skip=skip, limit=limit)
