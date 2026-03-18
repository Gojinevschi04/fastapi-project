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
RETRYABLE_ERROR_KEYWORDS = ["connection", "timeout", "network", "refused", "retries"]


async def get_due_tasks(session: AsyncSession) -> list[tuple[int, int]]:
    """Find scheduled tasks past their scheduled_time."""
    result = await session.exec(
        select(Task.id, Task.user_id).where(
            Task.status == TaskStatus.SCHEDULED,
            Task.scheduled_time <= datetime.now(),
        )
    )
    return list(result.all())


async def get_retryable_failed_tasks(session: AsyncSession) -> list[tuple[int, int]]:
    """Find failed tasks with network-related errors eligible for auto-retry.

    Tasks already retried (error_reason starts with '[RETRIED]') are skipped.
    """
    result = await session.exec(
        select(Task.id, Task.user_id, Task.error_reason).where(
            Task.status == TaskStatus.FAILED,
            Task.error_reason.isnot(None),
        )
    )
    retryable_tasks = []
    for task_id, user_id, error_reason in result.all():
        if not error_reason or error_reason.startswith("[RETRIED]"):
            continue
        error_lower = error_reason.lower()
        if any(keyword in error_lower for keyword in RETRYABLE_ERROR_KEYWORDS):
            retryable_tasks.append((task_id, user_id))
    return retryable_tasks


async def mark_task_for_retry(session: AsyncSession, task_id: int) -> None:
    """Reset a failed task to PENDING for retry, marking it as retried."""
    result = await session.exec(select(Task).where(Task.id == task_id))
    task = result.first()
    if task and task.status == TaskStatus.FAILED:
        original_error = task.error_reason or ""
        task.status = TaskStatus.PENDING
        task.error_reason = f"[RETRIED] {original_error}"
        task.summary = None
        session.add(task)
        await session.commit()
        logger.info("Task %d reset for retry (was: %s)", task_id, original_error[:100])


async def transition_task(session: AsyncSession, task_id: int) -> None:
    """Transition a single task from SCHEDULED to PENDING."""
    result = await session.exec(select(Task).where(Task.id == task_id))
    task = result.first()
    if task and task.status == TaskStatus.SCHEDULED:
        task.status = TaskStatus.PENDING
        session.add(task)
        await session.commit()
        logger.info("Task %d transitioned SCHEDULED → PENDING", task_id)


async def _process_due_tasks() -> None:
    """Find and execute all due scheduled tasks."""
    from app.modules.scheduler.task_executor import execute_due_task

    async with AsyncSession(engine) as session:
        due_tasks = await get_due_tasks(session)

    for task_id, user_id in due_tasks:
        try:
            async with AsyncSession(engine) as session:
                await transition_task(session, task_id)
            await execute_due_task(task_id, user_id)
        except Exception as process_error:
            logger.error("Failed to process task %d: %s", task_id, str(process_error))

    if due_tasks:
        logger.info("Processed %d due tasks", len(due_tasks))


async def _process_retryable_tasks() -> None:
    """Find and retry all failed tasks with network errors."""
    from app.modules.scheduler.task_executor import execute_due_task

    async with AsyncSession(engine) as session:
        retryable_tasks = await get_retryable_failed_tasks(session)

    for task_id, user_id in retryable_tasks:
        try:
            async with AsyncSession(engine) as session:
                await mark_task_for_retry(session, task_id)
            await execute_due_task(task_id, user_id)
        except Exception as retry_error:
            logger.error("Retry of task %d failed: %s", task_id, str(retry_error))

    if retryable_tasks:
        logger.info("Retried %d failed tasks", len(retryable_tasks))


async def run_scheduler() -> None:
    """Background polling loop for the worker process.

    Runs as a standalone process (app/worker.py), separate from the API.
    """
    logger.info("Task scheduler started (polling every %ds)", POLL_INTERVAL_SECONDS)

    while True:
        try:
            await _process_due_tasks()
            await _process_retryable_tasks()
        except Exception as scheduler_error:
            logger.error("Scheduler error: %s", str(scheduler_error))

        await asyncio.sleep(POLL_INTERVAL_SECONDS)
