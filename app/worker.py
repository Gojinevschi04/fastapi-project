"""Standalone worker process for scheduled task execution.

Runs independently from the API server. Polls the database every 30 seconds
for tasks with status=SCHEDULED and scheduled_time <= now, then auto-executes
them via the CallManager.

Usage:
    python -m app.worker

Architecture:
    - API server (app.main) handles HTTP requests only
    - Worker (this file) handles background task execution only
    - No Redis/Celery needed — simple asyncio polling loop
    - One worker instance should run at a time to avoid duplicate execution
"""

import asyncio

# Import all SQLModel table classes so metadata is fully populated.
# Without this, SQLModel cannot resolve foreign keys (e.g. Task.user_id → user.id)
# because the worker doesn't import routers like the API server does.
import app.modules.calls.models  # noqa: F401
import app.modules.files.models  # noqa: F401
import app.modules.tasks.models  # noqa: F401
import app.modules.templates.models  # noqa: F401
import app.modules.users.models  # noqa: F401
from app.core.logging import get_logger
from app.modules.scheduler.service import run_scheduler

logger = get_logger(__name__)


async def main() -> None:
    logger.info("Quiet Call AI worker starting...")
    logger.info("Polling for scheduled tasks every 30 seconds")
    await run_scheduler()


if __name__ == "__main__":
    asyncio.run(main())
