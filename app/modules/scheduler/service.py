import asyncio
from datetime import datetime

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import engine
from app.core.logging import get_logger
from app.modules.tasks.models import Task
from app.modules.tasks.schema import TaskStatus

logger = get_logger(__name__)

POLL_INTERVAL_SECONDS = 30


async def get_due_tasks(session: AsyncSession) -> list[Task]:
    """Find all tasks that are scheduled and past their scheduled_time."""
    now = datetime.now()
    result = await session.exec(
        select(Task).where(
            Task.status == TaskStatus.SCHEDULED,
            Task.scheduled_time <= now,
        )
    )
    return list(result.all())


async def run_scheduler() -> None:
    """Background loop that polls for due scheduled tasks and marks them as PENDING
    so the execute flow can pick them up.

    In production, this would directly trigger execute_task via a job queue.
    For the MVP, it transitions SCHEDULED → PENDING so the user can manually
    execute or an auto-execute hook can be added.
    """
    logger.info("Task scheduler started (polling every %ds)", POLL_INTERVAL_SECONDS)

    while True:
        try:
            async with AsyncSession(engine) as session:
                due_tasks = await get_due_tasks(session)

                for task in due_tasks:
                    logger.info(
                        "Task %d is due (scheduled for %s), transitioning to PENDING",
                        task.id,
                        task.scheduled_time,
                    )
                    task.status = TaskStatus.PENDING
                    session.add(task)

                if due_tasks:
                    await session.commit()
                    logger.info("Transitioned %d scheduled tasks to PENDING", len(due_tasks))

        except Exception as e:
            logger.error("Scheduler error: %s", str(e))

        await asyncio.sleep(POLL_INTERVAL_SECONDS)
