from collections.abc import Sequence

from sqlmodel import select

from core.repositories import Repository
from modules.users.models import User
from modules.users.schema import UserRole


class UserRepository(Repository):
    async def get_by_id(self, user_id: int) -> User | None:
        statement = select(User).where(User.id == user_id)
        result = await self._session.exec(statement)
        return result.first()

    async def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email)
        result = await self._session.exec(statement)
        return result.first()

    async def create(self, user: User) -> User:
        self._session.add(user)
        await self._session.commit()
        await self._session.refresh(user)
        return user

    async def update(self, user: User) -> User:
        self._session.add(user)
        await self._session.commit()
        await self._session.refresh(user)
        return user

    async def delete(self, user_id: int) -> bool:
        user = await self.get_by_id(user_id)
        if user:
            await self._session.delete(user)
            await self._session.commit()
            return True
        return False

    async def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[User]:
        statement = select(User).offset(skip).limit(limit)
        result = await self._session.exec(statement)
        return result.all()

    async def get_by_role(self, role: UserRole) -> Sequence[User]:
        statement = select(User).where(User.role == role)
        result = await self._session.exec(statement)
        return result.all()

    async def count(self) -> int:
        from sqlmodel import func

        statement = select(func.count(User.id))
        result = await self._session.exec(statement)
        return result.first() or 0

    async def get_all_paginated(self, skip: int = 0, limit: int = 100) -> tuple[Sequence[User], int]:
        users = await self.get_all(skip, limit)
        total = await self.count()
        return users, total

    async def update_user_role(self, user_id: int, role: UserRole) -> User | None:
        user = await self.get_by_id(user_id)
        if user:
            user.role = role
            return await self.update(user)
        return None
