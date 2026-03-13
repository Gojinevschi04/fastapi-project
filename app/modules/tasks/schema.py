import re
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, field_validator


class TaskStatus(StrEnum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


PHONE_REGEX = re.compile(r"^\+?[1-9]\d{7,14}$")


class TaskBase(BaseModel):
    target_phone: str
    template_id: int
    slot_data: dict[str, str] = {}
    scheduled_time: datetime | None = None

    @field_validator("target_phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not PHONE_REGEX.match(v):
            raise ValueError("Invalid phone number format. Expected: +XXXXXXXXXXX")
        return v


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    status: TaskStatus | None = None
    summary: str | None = None
    error_reason: str | None = None


class TaskResponse(BaseModel):
    id: int
    target_phone: str
    status: TaskStatus
    template_id: int
    template_name: str | None = None
    slot_data: dict[str, str]
    scheduled_time: datetime | None
    summary: str | None
    error_reason: str | None
    created_at: datetime
    updated_at: datetime


class TaskListResponse(BaseModel):
    items: list[TaskResponse]
    total: int
    limit: int
    offset: int


class TaskStatsResponse(BaseModel):
    total: int = 0
    pending: int = 0
    scheduled: int = 0
    in_progress: int = 0
    completed: int = 0
    failed: int = 0


class AdminStatsResponse(BaseModel):
    total_users: int = 0
    total_tasks: int = 0
    tasks_by_status: TaskStatsResponse = TaskStatsResponse()
    total_calls: int = 0
