from sqlmodel import Field

from app.core.models import BaseModel
from app.modules.users.schema import UserRole


class User(BaseModel, table=True):
    email: str | None = Field(index=True, nullable=True)
    role: UserRole = Field(default=UserRole.USER)
