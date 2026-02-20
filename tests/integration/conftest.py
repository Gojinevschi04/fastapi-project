from collections.abc import AsyncGenerator
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.database import get_db_session
from app.main import app
from app.modules.users.models import User
from app.modules.users.schema import UserRole


@pytest.fixture
def mock_user() -> User:
    return User(
        id=1,
        email="test@example.com",
        role=UserRole.USER,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def mock_admin_user() -> User:
    return User(
        id=2,
        email="admin@example.com",
        role=UserRole.ADMIN,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def mock_db_session() -> AsyncMock:
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = AsyncMock()
    session.exec = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


async def override_get_db_session() -> AsyncGenerator[AsyncMock, None]:
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = MagicMock()
    session.exec = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    try:
        yield session
    except:
        await session.rollback()
        raise
    finally:
        await session.close()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    app.dependency_overrides[get_db_session] = override_get_db_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def authenticated_client(mock_user: User) -> AsyncGenerator[AsyncClient, None]:
    async def get_user() -> User:
        return mock_user

    app.dependency_overrides[get_db_session] = override_get_db_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.pop(get_db_session, None)


@pytest_asyncio.fixture
async def admin_client(mock_admin_user: User) -> AsyncGenerator[AsyncClient, None]:
    async def get_user() -> User:
        return mock_admin_user

    async def get_admin() -> User:
        return mock_admin_user

    app.dependency_overrides[get_db_session] = override_get_db_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.pop(get_db_session, None)
