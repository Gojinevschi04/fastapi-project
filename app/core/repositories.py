from abc import ABC
from typing import Annotated

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_db_session


class Repository(ABC):
    def __init__(self, session: Annotated[AsyncSession, Depends(get_db_session)]) -> None:
        self._session = session
