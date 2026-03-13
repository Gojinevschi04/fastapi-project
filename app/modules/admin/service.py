from typing import Annotated

from fastapi import Depends

from app.core.logging import get_logger
from app.modules.calls.repository import CallSessionRepository
from app.modules.tasks.repository import TaskRepository
from app.modules.tasks.schema import AdminStatsResponse, TaskStatsResponse, TaskStatus
from app.modules.users.repository import UserRepository

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
