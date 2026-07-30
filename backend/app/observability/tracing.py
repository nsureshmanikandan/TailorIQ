"""OpenTelemetry tracing setup and helpers."""
import os
import logging

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource

logger = logging.getLogger(__name__)


def setup_tracing(service_name: str = "resumejdmatch-ai") -> None:
    """Initialize OpenTelemetry tracing.

    Configures a TracerProvider with OTLP exporter if the endpoint
    environment variable is set. Falls back to no-op if unavailable.
    """
    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)

    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if otlp_endpoint:
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                OTLPSpanExporter,
            )
            exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
            provider.add_span_processor(BatchSpanProcessor(exporter))
            logger.info("OTLP trace exporter configured: %s", otlp_endpoint)
        except ImportError:
            logger.warning("OTLP exporter not installed; tracing disabled")
    else:
        logger.info("No OTEL_EXPORTER_OTLP_ENDPOINT set; tracing in no-op mode")

    trace.set_tracer_provider(provider)


def get_tracer(name: str) -> trace.Tracer:
    """Get a named tracer instance."""
    return trace.get_tracer(name)
