from typing import Annotated

from fastapi import Depends

from collections.abc import Sequence

from app.core.logging import get_logger
from app.modules.calls.repository import CallSessionRepository
from app.modules.tasks.models import Task
from app.modules.tasks.repository import TaskRepository
from app.modules.tasks.schema import AdminStatsResponse, TaskStatsResponse, TaskStatus
from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.modules.users.schema import UserRole

logger = get_logger(__name__)


class AdminService:
    def __init__(
        self,
        user_repository: Annotated[UserRepository, Depends(UserRepository)],
        task_repository: Annotated[TaskRepository, Depends(TaskRepository)],
        call_session_repository: Annotated[CallSessionRepository, Depends(CallSessionRepository)],
    ) -> None:
        self.user_repository = user_repository
        self.task_repository = task_repository
        self.call_session_repository = call_session_repository

    async def get_system_stats(self) -> AdminStatsResponse:
        total_users = await self.user_repository.count()
        total_tasks = await self.task_repository.count_total()
        counts = await self.task_repository.count_by_status_all()
        total_calls = await self.call_session_repository.count_total()

        tasks_by_status = TaskStatsResponse(
            total=total_tasks,
            pending=counts.get(TaskStatus.PENDING, 0),
            scheduled=counts.get(TaskStatus.SCHEDULED, 0),
            in_progress=counts.get(TaskStatus.IN_PROGRESS, 0),
            completed=counts.get(TaskStatus.COMPLETED, 0),
            failed=counts.get(TaskStatus.FAILED, 0),
        )

        return AdminStatsResponse(
            total_users=total_users,
            total_tasks=total_tasks,
            tasks_by_status=tasks_by_status,
            total_calls=total_calls,
        )

    async def get_all_users(self, limit: int = 50, offset: int = 0) -> tuple[Sequence[User], int]:
        return await self.user_repository.get_all_paginated(offset, limit)

    async def get_all_tasks(
        self, limit: int = 50, offset: int = 0, status: TaskStatus | None = None
    ) -> tuple[Sequence[Task], int]:
        return await self.task_repository.get_all_paginated_admin(limit, offset, status)

    async def update_user_role(self, user_id: int, role: UserRole) -> User | None:
        return await self.user_repository.update_user_role(user_id, role)

    async def delete_user(self, user_id: int) -> bool:
        return await self.user_repository.delete(user_id)
