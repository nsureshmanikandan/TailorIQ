"""OpenTelemetry metrics setup."""
import logging

from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider

logger = logging.getLogger(__name__)

_meter: metrics.Meter | None = None


def setup_metrics(service_name: str = "resumejdmatch-ai") -> None:
    """Initialize OpenTelemetry metrics."""
    provider = MeterProvider()
    metrics.set_meter_provider(provider)
    global _meter
    _meter = metrics.get_meter(service_name)
    logger.info("Metrics provider initialized")


def get_meter() -> metrics.Meter:
    """Get the global meter instance."""
    if _meter is None:
        return metrics.get_meter("resumejdmatch-ai")
    return _meter
