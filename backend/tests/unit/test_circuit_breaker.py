"""Unit tests for the circuit breaker module."""

import time

import pytest

from app.orchestrator.circuit_breaker import CircuitBreaker, CircuitState


@pytest.fixture
def breaker():
    """Circuit breaker with short timers for testing."""
    return CircuitBreaker(
        fallback_deployment="fallback-model",
        failure_threshold=3,
        window_seconds=60.0,
        recovery_seconds=0.1,  # Short recovery for tests
    )


@pytest.mark.asyncio
class TestCircuitBreaker:
    """Tests for CircuitBreaker."""

    async def test_starts_closed(self, breaker: CircuitBreaker):
        """Circuit breaker starts in CLOSED state."""
        assert breaker.state == CircuitState.CLOSED

    async def test_returns_primary_when_closed(self, breaker: CircuitBreaker):
        """Returns primary deployment in closed state."""
        deployment = await breaker.get_deployment("primary-model")
        assert deployment == "primary-model"

    async def test_opens_after_threshold_failures(self, breaker: CircuitBreaker):
        """Opens after reaching failure threshold."""
        for _ in range(3):
            await breaker.record_failure()

        assert breaker.state == CircuitState.OPEN

    async def test_returns_fallback_when_open(self, breaker: CircuitBreaker):
        """Returns fallback deployment when circuit is open."""
        for _ in range(3):
            await breaker.record_failure()

        deployment = await breaker.get_deployment("primary-model")
        assert deployment == "fallback-model"

    async def test_transitions_to_half_open(self, breaker: CircuitBreaker):
        """Transitions to half-open after recovery period."""
        for _ in range(3):
            await breaker.record_failure()

        assert breaker.state == CircuitState.OPEN

        # Wait for recovery period
        import asyncio
        await asyncio.sleep(0.15)

        deployment = await breaker.get_deployment("primary-model")
        assert breaker.state == CircuitState.HALF_OPEN
        assert deployment == "primary-model"

    async def test_closes_on_success_after_half_open(self, breaker: CircuitBreaker):
        """Closes circuit after successful half-open probe."""
        for _ in range(3):
            await breaker.record_failure()

        import asyncio
        await asyncio.sleep(0.15)

        # Trigger half-open
        await breaker.get_deployment("primary-model")
        assert breaker.state == CircuitState.HALF_OPEN

        # Record success
        await breaker.record_success()
        assert breaker.state == CircuitState.CLOSED

    async def test_reopens_on_half_open_failure(self, breaker: CircuitBreaker):
        """Reopens circuit if half-open probe fails."""
        for _ in range(3):
            await breaker.record_failure()

        import asyncio
        await asyncio.sleep(0.15)

        await breaker.get_deployment("primary-model")
        assert breaker.state == CircuitState.HALF_OPEN

        await breaker.record_failure()
        assert breaker.state == CircuitState.OPEN

    async def test_reset_clears_state(self, breaker: CircuitBreaker):
        """Manual reset returns to closed state."""
        for _ in range(3):
            await breaker.record_failure()

        assert breaker.state == CircuitState.OPEN
        await breaker.reset()
        assert breaker.state == CircuitState.CLOSED

    async def test_get_status(self, breaker: CircuitBreaker):
        """Status dict contains expected fields."""
        status = breaker.get_status()
        assert status["state"] == "closed"
        assert status["failure_threshold"] == 3
        assert status["fallback_deployment"] == "fallback-model"

    async def test_failures_outside_window_dont_count(self):
        """Failures outside the time window are pruned."""
        breaker = CircuitBreaker(
            fallback_deployment="fallback",
            failure_threshold=3,
            window_seconds=0.05,  # Very short window
            recovery_seconds=0.1,
        )

        await breaker.record_failure()
        await breaker.record_failure()

        import asyncio
        await asyncio.sleep(0.06)  # Wait for window to expire

        await breaker.record_failure()
        # Should still be closed since older failures expired
        assert breaker.state == CircuitState.CLOSED
