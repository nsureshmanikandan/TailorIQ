"""Async retry logic with exponential backoff for agent LLM calls.

Retries on transient errors including rate limiting, service unavailability,
timeouts, and validation failures. Uses exponential backoff with jitter to
avoid thundering herd problems.
"""

import asyncio
import logging
import random
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, TypeVar

from openai import APIConnectionError, APITimeoutError, RateLimitError

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Default retry configuration
DEFAULT_MAX_RETRIES = 2
DEFAULT_BASE_DELAY_SECONDS = 1.0
DEFAULT_MAX_DELAY_SECONDS = 8.0
DEFAULT_JITTER_FACTOR = 0.1


class RetryExhaustedError(Exception):
    """Raised when all retry attempts have been exhausted.

    Attributes:
        last_error: The last exception that caused the final retry to fail.
        attempts: Total number of attempts made.
    """

    def __init__(self, last_error: Exception, attempts: int) -> None:
        self.last_error = last_error
        self.attempts = attempts
        super().__init__(
            f"All {attempts} retry attempts exhausted. Last error: {last_error}"
        )


class ServiceUnavailableError(Exception):
    """Raised when the LLM service is temporarily unavailable."""


class ValidationError(Exception):
    """Raised when LLM output fails schema validation (retryable)."""


# Exceptions that are safe to retry
RETRYABLE_EXCEPTIONS: tuple[type[Exception], ...] = (
    RateLimitError,
    APIConnectionError,
    ServiceUnavailableError,
    TimeoutError,
    APITimeoutError,
    ValidationError,
    ConnectionError,
    asyncio.TimeoutError,
)


def _compute_delay(
    attempt: int,
    base_delay: float,
    max_delay: float,
    jitter_factor: float,
) -> float:
    """Compute exponential backoff delay with jitter.

    Args:
        attempt: Zero-indexed attempt number (0 = first retry).
        base_delay: Base delay in seconds.
        max_delay: Maximum delay cap in seconds.
        jitter_factor: Fraction of delay to randomize (0.0 - 1.0).

    Returns:
        Delay in seconds before the next retry.
    """
    # Exponential backoff: base_delay * 2^attempt
    delay = base_delay * (2**attempt)
    delay = min(delay, max_delay)

    # Add jitter to prevent thundering herd
    jitter = delay * jitter_factor * random.uniform(-1, 1)
    return max(0.0, delay + jitter)


async def retry_with_backoff(
    func: Callable[..., Awaitable[T]],
    *args: Any,
    max_retries: int = DEFAULT_MAX_RETRIES,
    base_delay: float = DEFAULT_BASE_DELAY_SECONDS,
    max_delay: float = DEFAULT_MAX_DELAY_SECONDS,
    jitter_factor: float = DEFAULT_JITTER_FACTOR,
    retryable_exceptions: tuple[type[Exception], ...] = RETRYABLE_EXCEPTIONS,
    **kwargs: Any,
) -> T:
    """Execute an async function with exponential backoff retry logic.

    Args:
        func: The async function to call.
        *args: Positional arguments for the function.
        max_retries: Maximum number of retry attempts (default: 2).
        base_delay: Base delay between retries in seconds (default: 1.0).
        max_delay: Maximum delay cap in seconds (default: 8.0).
        jitter_factor: Jitter fraction for delay randomization (default: 0.1).
        retryable_exceptions: Tuple of exception types that trigger retry.
        **kwargs: Keyword arguments for the function.

    Returns:
        The return value of the function on success.

    Raises:
        RetryExhaustedError: When all retries are exhausted.
        Exception: Non-retryable exceptions are re-raised immediately.
    """
    last_error: Exception | None = None
    total_attempts = max_retries + 1  # initial attempt + retries

    for attempt in range(total_attempts):
        try:
            return await func(*args, **kwargs)
        except retryable_exceptions as e:
            last_error = e
            if attempt < max_retries:
                delay = _compute_delay(attempt, base_delay, max_delay, jitter_factor)
                logger.warning(
                    "Retry %d/%d for %s after %s: %.2fs delay",
                    attempt + 1,
                    max_retries,
                    func.__name__ if hasattr(func, "__name__") else str(func),
                    type(e).__name__,
                    delay,
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    "All %d retries exhausted for %s. Last error: %s",
                    max_retries,
                    func.__name__ if hasattr(func, "__name__") else str(func),
                    str(e),
                )

    raise RetryExhaustedError(last_error=last_error, attempts=total_attempts)  # type: ignore[arg-type]


def with_retry(
    max_retries: int = DEFAULT_MAX_RETRIES,
    base_delay: float = DEFAULT_BASE_DELAY_SECONDS,
    max_delay: float = DEFAULT_MAX_DELAY_SECONDS,
    jitter_factor: float = DEFAULT_JITTER_FACTOR,
    retryable_exceptions: tuple[type[Exception], ...] = RETRYABLE_EXCEPTIONS,
) -> Callable:
    """Decorator for adding retry logic to async functions.

    Args:
        max_retries: Maximum number of retry attempts.
        base_delay: Base delay between retries in seconds.
        max_delay: Maximum delay cap in seconds.
        jitter_factor: Jitter fraction for delay randomization.
        retryable_exceptions: Tuple of exception types that trigger retry.

    Returns:
        Decorated async function with retry logic.

    Example:
        @with_retry(max_retries=2, base_delay=1.0)
        async def call_llm(prompt: str) -> dict:
            ...
    """

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            return await retry_with_backoff(
                func,
                *args,
                max_retries=max_retries,
                base_delay=base_delay,
                max_delay=max_delay,
                jitter_factor=jitter_factor,
                retryable_exceptions=retryable_exceptions,
                **kwargs,
            )

        return wrapper

    return decorator
