from collections.abc import Sequence
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.modules.users.schema import UserRole


@pytest.mark.asyncio
async def test_get_by_id(mock_session: MagicMock, mock_user: User) -> None:
    mock_result = MagicMock()
    mock_result.first.return_value = mock_user
    mock_session.exec.return_value = mock_result

    repo = UserRepository(session=mock_session)
    result = await repo.get_by_id(1)

    assert result == mock_user


@pytest.mark.asyncio
async def test_get_by_email(mock_session: MagicMock, mock_user: User) -> None:
    mock_result = MagicMock()
    mock_result.first.return_value = mock_user
    mock_session.exec.return_value = mock_result

    repo = UserRepository(session=mock_session)
    result = await repo.get_by_email("test@example.com")

    assert result == mock_user


@pytest.mark.asyncio
async def test_create(mock_session: MagicMock, mock_user: User) -> None:
    mock_session.refresh = AsyncMock()

    repo = UserRepository(session=mock_session)
    result = await repo.create(mock_user)

    mock_session.add.assert_called_once_with(mock_user)
    mock_session.commit.assert_called_once()
    assert result == mock_user


@pytest.mark.asyncio
async def test_update(mock_session: MagicMock, mock_user: User) -> None:
    mock_session.refresh = AsyncMock()

    repo = UserRepository(session=mock_session)
    result = await repo.update(mock_user)

    mock_session.add.assert_called_once_with(mock_user)
    mock_session.commit.assert_called_once()
    assert result == mock_user


@pytest.mark.asyncio
async def test_delete_success(mock_session: MagicMock, mock_user: User) -> None:
    mock_result = MagicMock()
    mock_result.first.return_value = mock_user
    mock_session.exec.return_value = mock_result
    mock_session.delete = AsyncMock()

    repo = UserRepository(session=mock_session)
    result = await repo.delete(1)

    assert result is True
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_delete_not_found(mock_session: MagicMock) -> None:
    mock_result = MagicMock()
    mock_result.first.return_value = None
    mock_session.exec.return_value = mock_result

    repo = UserRepository(session=mock_session)
    result = await repo.delete(999)

    assert result is False


@pytest.mark.asyncio
async def test_get_all(mock_session: MagicMock) -> None:
    users = [User(id=i, email=f"user{i}@example.com") for i in range(3)]
    mock_result = MagicMock()
    mock_result.all.return_value = users
    mock_session.exec.return_value = mock_result

    repo = UserRepository(session=mock_session)
    result = await repo.get_all(skip=0, limit=100)

    assert isinstance(result, Sequence)
    assert len(result) == 3


@pytest.mark.asyncio
async def test_get_by_role(mock_session: MagicMock) -> None:
    users = [User(id=1, email="admin@example.com", role=UserRole.ADMIN)]
    mock_result = MagicMock()
    mock_result.all.return_value = users
    mock_session.exec.return_value = mock_result

    repo = UserRepository(session=mock_session)
    result = await repo.get_by_role(UserRole.ADMIN)

    assert len(result) == 1
    assert result[0].role == UserRole.ADMIN


@pytest.mark.asyncio
async def test_count(mock_session: MagicMock) -> None:
    mock_result = MagicMock()
    mock_result.first.return_value = 5
    mock_session.exec.return_value = mock_result

    repo = UserRepository(session=mock_session)
    result = await repo.count()

    assert result == 5


@pytest.mark.asyncio
async def test_get_all_paginated(mock_session: MagicMock) -> None:
    users = [User(id=i, email=f"user{i}@example.com") for i in range(3)]
    mock_result_all = MagicMock()
    mock_result_all.all.return_value = users
    mock_result_count = MagicMock()
    mock_result_count.first.return_value = 3
    mock_session.exec.side_effect = [mock_result_all, mock_result_count]

    repo = UserRepository(session=mock_session)
    result_users, total = await repo.get_all_paginated(skip=0, limit=100)

    assert len(result_users) == 3
    assert total == 3


@pytest.mark.asyncio
async def test_update_user_role(mock_session: MagicMock, mock_user: User) -> None:
    mock_result = MagicMock()
    mock_result.first.return_value = mock_user
    mock_session.exec.return_value = mock_result
    mock_session.refresh = AsyncMock()

    repo = UserRepository(session=mock_session)
    result = await repo.update_user_role(1, UserRole.ADMIN)

    assert result is not None
    assert result.role == UserRole.ADMIN


@pytest.mark.asyncio
async def test_update_user_role_not_found(mock_session: MagicMock) -> None:
    mock_result = MagicMock()
    mock_result.first.return_value = None
    mock_session.exec.return_value = mock_result

    repo = UserRepository(session=mock_session)
    result = await repo.update_user_role(999, UserRole.ADMIN)

    assert result is None
