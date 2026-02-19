from sqlmodel import Field

from core.models import BaseModel
from modules.users.schema import UserRole


class User(BaseModel, table=True):
    email: str | None = Field(index=True, nullable=True)
    role: UserRole = Field(default=UserRole.USER)
