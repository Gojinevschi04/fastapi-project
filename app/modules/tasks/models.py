from datetime import datetime

from sqlalchemy import JSON
from sqlmodel import Column, Field

from app.core.models import BaseModel
from app.modules.tasks.schema import TaskStatus


class Task(BaseModel, table=True):
    target_phone: str = Field(nullable=False)
    status: TaskStatus = Field(default=TaskStatus.PENDING, index=True, nullable=False)
    template_id: int = Field(foreign_key="dialog_template.id", nullable=False)
    user_id: int = Field(foreign_key="user.id", nullable=False, index=True)
    slot_data: dict[str, str] = Field(default={}, sa_column=Column(JSON, nullable=False))
    scheduled_time: datetime | None = Field(default=None, nullable=True, index=True)
    summary: str | None = Field(default=None, nullable=True)
    error_reason: str | None = Field(default=None, nullable=True)
