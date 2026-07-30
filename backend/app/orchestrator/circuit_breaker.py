"""Circuit breaker pattern for LLM model fallback.

Tracks failure counts per deployment model. When failures exceed a threshold
within a time window, the circuit opens and subsequent calls are routed to
the configured fallback deployment. The circuit auto-recovers after a
configurable recovery period.

States:
    CLOSED: Normal operation, requests go to the primary model.
    OPEN: Primary model is failing, requests go to the fallback model.
    HALF_OPEN: Recovery period elapsed, next request tests the primary model.
"""

import asyncio
import logging
import time
from enum import Enum

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    """Circuit breaker state machine."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Circuit breaker for LLM deployment failover.

    Monitors failure rates per model deployment and automatically routes
    traffic to a fallback deployment when the primary model is unhealthy.

    Attributes:
        failure_threshold: Number of failures that trigger the circuit to open.
        window_seconds: Time window in which failures are counted.
        recovery_seconds: Time to wait before attempting recovery (half-open).
    """

    def __init__(
        self,
        fallback_deployment: str,
        failure_threshold: int = 3,
        window_seconds: float = 60.0,
        recovery_seconds: float = 30.0,
    ) -> None:
        """Initialize the circuit breaker.

        Args:
            fallback_deployment: Deployment name to use when circuit is open.
            failure_threshold: Number of failures in window before opening circuit.
            window_seconds: Sliding window duration for failure counting (seconds).
            recovery_seconds: Duration before attempting half-open recovery (seconds).
        """
        self._fallback_deployment = fallback_deployment
        self._failure_threshold = failure_threshold
        self._window_seconds = window_seconds
        self._recovery_seconds = recovery_seconds

        self._state = CircuitState.CLOSED
        self._failures: list[float] = []  # Timestamps of recent failures
        self._last_opened_at: float = 0.0
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        """Current circuit breaker state."""
        return self._state

    @property
    def fallback_deployment(self) -> str:
        """The fallback deployment name."""
        return self._fallback_deployment

    async def get_deployment(self, primary_deployment: str) -> str:
        """Get the deployment to use based on circuit state.

        Args:
            primary_deployment: The preferred primary deployment name.

        Returns:
            The deployment name to use (primary or fallback).
        """
        async with self._lock:
            self._prune_old_failures()

            if self._state == CircuitState.CLOSED:
                return primary_deployment

            if self._state == CircuitState.OPEN:
                # Check if recovery period has elapsed
                elapsed = time.monotonic() - self._last_opened_at
                if elapsed >= self._recovery_seconds:
                    self._state = CircuitState.HALF_OPEN
                    logger.info(
                        "Circuit breaker transitioning to HALF_OPEN after %.1fs recovery period",
                        elapsed,
                    )
                    return primary_deployment  # Test the primary
                return self._fallback_deployment

            # HALF_OPEN: let it through to the primary for testing
            return primary_deployment

    async def record_success(self) -> None:
        """Record a successful request, potentially closing the circuit."""
        async with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.CLOSED
                self._failures.clear()
                logger.info("Circuit breaker CLOSED after successful half-open probe.")

    async def record_failure(self) -> None:
        """Record a failed request, potentially opening the circuit."""
        async with self._lock:
            now = time.monotonic()
            self._failures.append(now)
            self._prune_old_failures()

            if self._state == CircuitState.HALF_OPEN:
                # Half-open probe failed, reopen the circuit
                self._state = CircuitState.OPEN
                self._last_opened_at = now
                logger.warning(
                    "Circuit breaker re-OPENED after half-open probe failure."
                )
                return

            if (
                self._state == CircuitState.CLOSED
                and len(self._failures) >= self._failure_threshold
            ):
                self._state = CircuitState.OPEN
                self._last_opened_at = now
                logger.warning(
                    "Circuit breaker OPENED: %d failures in %.1fs window. "
                    "Falling back to deployment: %s",
                    len(self._failures),
                    self._window_seconds,
                    self._fallback_deployment,
                )

    def _prune_old_failures(self) -> None:
        """Remove failures outside the current time window."""
        cutoff = time.monotonic() - self._window_seconds
        self._failures = [ts for ts in self._failures if ts > cutoff]

    async def reset(self) -> None:
        """Manually reset the circuit breaker to CLOSED state."""
        async with self._lock:
            self._state = CircuitState.CLOSED
            self._failures.clear()
            self._last_opened_at = 0.0
            logger.info("Circuit breaker manually reset to CLOSED.")

    def get_status(self) -> dict:
        """Get current circuit breaker status for monitoring.

        Returns:
            Dictionary with state, failure count, and configuration details.
        """
        return {
            "state": self._state.value,
            "failure_count": len(self._failures),
            "failure_threshold": self._failure_threshold,
            "window_seconds": self._window_seconds,
            "recovery_seconds": self._recovery_seconds,
            "fallback_deployment": self._fallback_deployment,
        }
