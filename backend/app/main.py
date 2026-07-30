"""FastAPI application factory and lifespan management.

This module creates the FastAPI application instance with:
- Async lifespan for startup/shutdown resource management
- CORS middleware configured from environment
- Global exception handlers for consistent error responses
- API router registration
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.api import router as api_router
from app.config import get_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown lifecycle.

    Startup:
        - Load configuration and validate
        - Log application start with environment info

    Shutdown:
        - Clean up resources (database connections, HTTP clients)
        - Log graceful shutdown
    """
    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    logger.info(
        "Application starting",
        extra={"env": settings.APP_ENV, "service": settings.OTEL_SERVICE_NAME},
    )
    yield
    logger.info("Application shutting down")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    settings = get_settings()

    app = FastAPI(
        title="ResumeJDMatch AI",
        description="AI-powered resume-to-JD alignment and optimization platform",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
    )

    # ─── CORS Middleware ─────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ─── Exception Handlers ──────────────────────────────────────────────────
    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
        """Handle Pydantic validation errors with a structured response."""
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "validation_error",
                "detail": exc.errors(include_url=False),
            },
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        """Handle business logic value errors."""
        logger.warning("ValueError in request %s: %s", request.url.path, str(exc))
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "bad_request",
                "detail": str(exc),
            },
        )

    @app.exception_handler(PermissionError)
    async def permission_error_handler(request: Request, exc: PermissionError) -> JSONResponse:
        """Handle permission/authorization errors."""
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "error": "forbidden",
                "detail": str(exc),
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Catch-all handler for unexpected exceptions.

        Logs the full traceback but returns a generic message to the client
        to avoid leaking internal details.
        """
        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "internal_server_error",
                "detail": "An unexpected error occurred. Please try again later.",
            },
        )

    # ─── Router Registration ─────────────────────────────────────────────────
    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_app()
