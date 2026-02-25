from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.modules.users.schema import UserCreate, UserListResponse, UserResponse, UserRole, UserUpdate
from app.modules.users.service import UserService


@pytest.mark.asyncio
async def test_create_user_success(mock_session: MagicMock) -> None:
    mock_user_repo = MagicMock(spec=UserRepository)
    mock_user_repo.get_by_email = AsyncMock(return_value=None)
    new_user = User(id=1, email="new@example.com", role=UserRole.USER)
    mock_user_repo.create = AsyncMock(return_value=new_user)

    service = UserService(user_repository=mock_user_repo)
    user_data = UserCreate(email="new@example.com", role=UserRole.USER, password="testpass123")
    result = await service.create_user(user_data)

    assert isinstance(result, UserResponse)
    assert result.email == "new@example.com"


@pytest.mark.asyncio
async def test_create_user_duplicate_email(mock_session: MagicMock, mock_user: User) -> None:
    mock_user_repo = MagicMock(spec=UserRepository)
    mock_user_repo.get_by_email = AsyncMock(return_value=mock_user)

    service = UserService(user_repository=mock_user_repo)
    user_data = UserCreate(email="test@example.com", role=UserRole.USER, password="testpass123")
    with pytest.raises(ValueError):
        await service.create_user(user_data)


@pytest.mark.asyncio
async def test_update_user_success(mock_session: MagicMock, mock_user: User) -> None:
    mock_user_repo = MagicMock(spec=UserRepository)
    mock_user_repo.get_by_id = AsyncMock(return_value=mock_user)
    mock_user_repo.get_by_email = AsyncMock(return_value=None)
    updated_user = User(id=1, email="updated@example.com", role=UserRole.ADMIN)
    mock_user_repo.update = AsyncMock(return_value=updated_user)

    service = UserService(user_repository=mock_user_repo)
    user_data = UserUpdate(email="updated@example.com", role=UserRole.ADMIN)
    result = await service.update_user(1, user_data)

    assert isinstance(result, UserResponse)
    assert result.email == "updated@example.com"


@pytest.mark.asyncio
async def test_update_user_not_found(mock_session: MagicMock) -> None:
    mock_user_repo = MagicMock(spec=UserRepository)
    mock_user_repo.get_by_id = AsyncMock(return_value=None)

    service = UserService(user_repository=mock_user_repo)
    user_data = UserUpdate(email="updated@example.com")
    result = await service.update_user(999, user_data)

    assert result is None


@pytest.mark.asyncio
async def test_delete_user_success(mock_session: MagicMock) -> None:
    mock_user_repo = MagicMock(spec=UserRepository)
    mock_user_repo.delete = AsyncMock(return_value=True)

    service = UserService(user_repository=mock_user_repo)
    result = await service.delete_user(1)

    assert result is True


@pytest.mark.asyncio
async def test_get_user_success(mock_session: MagicMock, mock_user: User) -> None:
    mock_user_repo = MagicMock(spec=UserRepository)
    mock_user_repo.get_by_id = AsyncMock(return_value=mock_user)

    service = UserService(user_repository=mock_user_repo)
    result = await service.get_user(1)

    assert isinstance(result, UserResponse)
    assert result.id == mock_user.id


@pytest.mark.asyncio
async def test_get_user_not_found(mock_session: MagicMock) -> None:
    mock_user_repo = MagicMock(spec=UserRepository)
    mock_user_repo.get_by_id = AsyncMock(return_value=None)

    service = UserService(user_repository=mock_user_repo)
    result = await service.get_user(999)

    assert result is None


@pytest.mark.asyncio
async def test_get_users(mock_session: MagicMock) -> None:
    mock_user_repo = MagicMock(spec=UserRepository)
    users = [User(id=i, email=f"user{i}@example.com") for i in range(3)]
    mock_user_repo.get_all_paginated = AsyncMock(return_value=(users, 3))

    service = UserService(user_repository=mock_user_repo)
    result = await service.get_users(skip=0, limit=100)

    assert isinstance(result, UserListResponse)
    assert result.total == 3
