"""Global concurrency controls for outbound call execution.

Prevents the API and worker from spawning unlimited concurrent Twilio calls
(e.g., if a user rapid-clicks Execute or the scheduler finds many due tasks
at once). Twilio trial accounts allow 1 concurrent call; paid plans vary.
"""

import asyncio

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_call_semaphore: asyncio.Semaphore | None = None


def get_call_semaphore() -> asyncio.Semaphore:
    """Return a process-local semaphore that caps concurrent outbound calls.

    Created lazily so the limit reads from settings at first use (makes tests
    that patch MAX_CONCURRENT_CALLS before first call work as expected).
    """
    global _call_semaphore
    if _call_semaphore is None:
        _call_semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_CALLS)
        logger.info("Call concurrency semaphore initialized: max=%d",
                    settings.MAX_CONCURRENT_CALLS)
    return _call_semaphore


def reset_call_semaphore() -> None:
    """Reset the singleton — test-only helper."""
    global _call_semaphore
    _call_semaphore = None
