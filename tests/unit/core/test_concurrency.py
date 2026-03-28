import asyncio
from unittest.mock import patch

import pytest

from app.core.concurrency import get_call_semaphore, reset_call_semaphore


def setup_function() -> None:
    reset_call_semaphore()


def teardown_function() -> None:
    reset_call_semaphore()


def test_get_call_semaphore_respects_configured_max() -> None:
    with patch("app.core.concurrency.settings.MAX_CONCURRENT_CALLS", 3):
        reset_call_semaphore()
        semaphore = get_call_semaphore()
        assert semaphore._value == 3


def test_get_call_semaphore_is_singleton() -> None:
    first = get_call_semaphore()
    second = get_call_semaphore()
    assert first is second


@pytest.mark.asyncio
async def test_semaphore_blocks_after_max_concurrent_acquired() -> None:
    with patch("app.core.concurrency.settings.MAX_CONCURRENT_CALLS", 2):
        reset_call_semaphore()
        semaphore = get_call_semaphore()

        await semaphore.acquire()
        await semaphore.acquire()

        assert semaphore.locked()

        try:
            await asyncio.wait_for(semaphore.acquire(), timeout=0.05)
        except TimeoutError:
            pass
        else:
            raise AssertionError("Expected third acquire to block")

        semaphore.release()
        semaphore.release()


@pytest.mark.asyncio
async def test_semaphore_releases_when_context_exits() -> None:
    with patch("app.core.concurrency.settings.MAX_CONCURRENT_CALLS", 1):
        reset_call_semaphore()
        semaphore = get_call_semaphore()

        async with semaphore:
            assert semaphore.locked()

        assert not semaphore.locked()
