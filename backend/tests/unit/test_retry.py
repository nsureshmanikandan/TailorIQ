"""Unit tests for the retry logic module."""

import asyncio

import pytest

from app.orchestrator.retry import (
    RetryExhaustedError,
    ServiceUnavailableError,
    ValidationError,
    retry_with_backoff,
    with_retry,
)


@pytest.mark.asyncio
class TestRetryWithBackoff:
    """Tests for retry_with_backoff function."""

    async def test_succeeds_first_try(self):
        """Function succeeding on first call returns immediately."""
        call_count = 0

        async def success():
            nonlocal call_count
            call_count += 1
            return "ok"

        result = await retry_with_backoff(success, base_delay=0.01)
        assert result == "ok"
        assert call_count == 1

    async def test_retries_on_retryable_error(self):
        """Function is retried on retryable exceptions."""
        call_count = 0

        async def fails_then_succeeds():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ServiceUnavailableError("service down")
            return "recovered"

        result = await retry_with_backoff(
            fails_then_succeeds, max_retries=2, base_delay=0.01
        )
        assert result == "recovered"
        assert call_count == 3

    async def test_exhausts_retries(self):
        """Raises RetryExhaustedError when all retries fail."""

        async def always_fails():
            raise ServiceUnavailableError("always down")

        with pytest.raises(RetryExhaustedError) as exc_info:
            await retry_with_backoff(always_fails, max_retries=2, base_delay=0.01)

        assert exc_info.value.attempts == 3
        assert isinstance(exc_info.value.last_error, ServiceUnavailableError)

    async def test_non_retryable_error_propagates(self):
        """Non-retryable exceptions are raised immediately."""

        async def raises_value_error():
            raise ValueError("not retryable")

        with pytest.raises(ValueError, match="not retryable"):
            await retry_with_backoff(raises_value_error, max_retries=2, base_delay=0.01)

    async def test_retries_on_timeout(self):
        """Retries on TimeoutError."""
        call_count = 0

        async def timeout_then_ok():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise TimeoutError("timed out")
            return "done"

        result = await retry_with_backoff(timeout_then_ok, max_retries=2, base_delay=0.01)
        assert result == "done"
        assert call_count == 2

    async def test_retries_on_validation_error(self):
        """Retries on ValidationError."""
        call_count = 0

        async def validation_then_ok():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValidationError("bad schema")
            return "valid"

        result = await retry_with_backoff(
            validation_then_ok, max_retries=2, base_delay=0.01
        )
        assert result == "valid"
        assert call_count == 2


@pytest.mark.asyncio
class TestWithRetryDecorator:
    """Tests for the @with_retry decorator."""

    async def test_decorator_success(self):
        """Decorated function works on success."""

        @with_retry(max_retries=1, base_delay=0.01)
        async def simple():
            return 42

        result = await simple()
        assert result == 42

    async def test_decorator_retries(self):
        """Decorated function retries on failure."""
        call_count = 0

        @with_retry(max_retries=2, base_delay=0.01)
        async def fails_once():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ServiceUnavailableError("down")
            return "up"

        result = await fails_once()
        assert result == "up"
        assert call_count == 2
