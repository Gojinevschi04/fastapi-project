import pytest

from app.core.retry import async_retry


@pytest.mark.asyncio
async def test_retry_succeeds_first_try() -> None:
    call_count = 0

    @async_retry(max_retries=3, delay=0.01)
    async def success() -> str:
        nonlocal call_count
        call_count += 1
        return "ok"

    result = await success()
    assert result == "ok"
    assert call_count == 1


@pytest.mark.asyncio
async def test_retry_succeeds_after_failures() -> None:
    call_count = 0

    @async_retry(max_retries=3, delay=0.01)
    async def flaky() -> str:
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError("connection lost")
        return "recovered"

    result = await flaky()
    assert result == "recovered"
    assert call_count == 3


@pytest.mark.asyncio
async def test_retry_raises_after_all_attempts() -> None:
    call_count = 0

    @async_retry(max_retries=3, delay=0.01)
    async def always_fail() -> str:
        nonlocal call_count
        call_count += 1
        raise TimeoutError("timed out")

    with pytest.raises(TimeoutError, match="timed out"):
        await always_fail()
    assert call_count == 3


@pytest.mark.asyncio
async def test_retry_does_not_retry_non_retryable() -> None:
    call_count = 0

    @async_retry(max_retries=3, delay=0.01, retryable_errors=(ConnectionError,))
    async def value_error() -> str:
        nonlocal call_count
        call_count += 1
        raise ValueError("not retryable")

    with pytest.raises(ValueError, match="not retryable"):
        await value_error()
    assert call_count == 1  # no retries for ValueError


@pytest.mark.asyncio
async def test_retry_exponential_backoff() -> None:
    """Verify it doesn't hang — completes quickly with small delays."""
    call_count = 0

    @async_retry(max_retries=3, delay=0.01, backoff=2.0)
    async def fail_twice() -> str:
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise OSError("network error")
        return "ok"

    result = await fail_twice()
    assert result == "ok"
    assert call_count == 3
