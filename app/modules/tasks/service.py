from collections.abc import Sequence
from typing import Annotated

from fastapi import Depends

from app.core.logging import get_logger
from app.modules.tasks.exceptions import InvalidTaskDataError, TaskNotCancellableError, TaskNotFoundError
from app.modules.tasks.models import Task
from app.modules.tasks.repository import TaskRepository
from app.modules.tasks.schema import TaskCreate, TaskStatsResponse, TaskStatus
from app.modules.templates.exceptions import TemplateNotFoundError
from app.modules.templates.repository import TemplateRepository

logger = get_logger(__name__)


class TaskService:
    def __init__(
        self,
        task_repository: Annotated[TaskRepository, Depends(TaskRepository)],
        template_repository: Annotated[TemplateRepository, Depends(TemplateRepository)],
    ) -> None:
        self.task_repository = task_repository
        self.template_repository = template_repository

    async def create_task(self, data: TaskCreate, user_id: int) -> Task:
        template = await self.template_repository.get_by_id(data.template_id)
        if not template:
            raise TemplateNotFoundError(f"Template with id {data.template_id} not found")

        missing_slots = [slot for slot in template.required_slots if slot not in data.slot_data]
        if missing_slots:
            raise InvalidTaskDataError(f"Missing required slots: {', '.join(missing_slots)}")

        status = TaskStatus.SCHEDULED if data.scheduled_time else TaskStatus.PENDING

        task = Task(
            target_phone=data.target_phone,
            status=status,
            template_id=data.template_id,
            user_id=user_id,
            slot_data=data.slot_data,
            scheduled_time=data.scheduled_time,
        )

        logger.info("Creating task for user %s with template %s", user_id, template.name)
        return await self.task_repository.create(task)

    async def get_task(self, task_id: int, user_id: int, is_admin: bool = False) -> Task:
        if is_admin:
            task = await self.task_repository.get_by_id_any_user(task_id)
        else:
            task = await self.task_repository.get_by_id(task_id, user_id)
        if not task:
            raise TaskNotFoundError(f"Task with id {task_id} not found")
        return task

    async def get_tasks(
        self,
        user_id: int,
        limit: int = 20,
        offset: int = 0,
        status: TaskStatus | None = None,
    ) -> tuple[Sequence[Task], int]:
        return await self.task_repository.get_all_paginated(user_id, limit, offset, status)

    async def cancel_task(self, task_id: int, user_id: int) -> Task:
        task = await self.task_repository.get_by_id(task_id, user_id)
        if not task:
            raise TaskNotFoundError(f"Task with id {task_id} not found")

        if task.status not in (TaskStatus.PENDING, TaskStatus.SCHEDULED):
            raise TaskNotCancellableError(f"Task with status '{task.status}' cannot be cancelled")

        task.status = TaskStatus.FAILED
        task.error_reason = "Cancelled by user"
        return await self.task_repository.update(task)

    async def get_stats(self, user_id: int) -> TaskStatsResponse:
        counts = await self.task_repository.count_by_status(user_id)
        return TaskStatsResponse(
            total=sum(counts.values()),
            pending=counts.get(TaskStatus.PENDING, 0),
            scheduled=counts.get(TaskStatus.SCHEDULED, 0),
            in_progress=counts.get(TaskStatus.IN_PROGRESS, 0),
            completed=counts.get(TaskStatus.COMPLETED, 0),
            failed=counts.get(TaskStatus.FAILED, 0),
        )
