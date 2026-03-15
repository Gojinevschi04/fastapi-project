"""Async retry decorator for transient network failures."""

import asyncio
import functools
from collections.abc import Callable
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)

# Exceptions considered retryable (transient network issues)
RETRYABLE_ERRORS = (
    ConnectionError,
    TimeoutError,
    OSError,
)


def async_retry(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    retryable_errors: tuple = RETRYABLE_ERRORS,
) -> Callable:
    """Decorator that retries async functions on transient failures.

    Args:
        max_retries: Maximum number of retry attempts.
        delay: Initial delay between retries (seconds).
        backoff: Multiplier for delay on each retry (exponential backoff).
        retryable_errors: Tuple of exception types to retry on.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_error: Exception | None = None
            current_delay = delay

            for attempt in range(1, max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except retryable_errors as e:
                    last_error = e
                    if attempt < max_retries:
                        logger.warning(
                            "%s failed (attempt %d/%d): %s — retrying in %.1fs",
                            func.__name__,
                            attempt,
                            max_retries,
                            str(e),
                            current_delay,
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            "%s failed after %d attempts: %s",
                            func.__name__,
                            max_retries,
                            str(e),
                        )

            raise last_error  # type: ignore[misc]

        return wrapper

    return decorator
