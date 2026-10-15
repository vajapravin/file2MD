"""FastAPI application factory and lifecycle management."""

import logging
import sys
import structlog
from fastapi import FastAPI

# Raise recursion limit to prevent recursion errors on deeply nested PDF/HTML trees
sys.setrecursionlimit(10000)
from file2md.api.v1.router import api_v1_router
from file2md.config import Settings, get_settings
from file2md.middleware.cors import setup_cors
from file2md.middleware.error_handler import register_error_handlers


def configure_logging(settings: Settings) -> None:
    """Configure structured logging using structlog without leaking file contents."""
    log_level = getattr(logging, settings.APP_LOG_LEVEL.upper(), logging.INFO)
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=log_level)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer()
            if settings.APP_ENV != "development"
            else structlog.dev.ConsoleRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure a file2MD FastAPI instance."""
    if settings is None:
        settings = get_settings()

    configure_logging(settings)

    app = FastAPI(
        title="file2MD API",
        version=settings.APP_VERSION,
        description="Modular service for converting multi-format files to clean Markdown using markitdown.",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Setup Middleware
    setup_cors(app, settings.CORS_ALLOWED_ORIGINS)
    register_error_handlers(app)

    # Register Routers
    app.include_router(api_v1_router, prefix="/api/v1")

    return app


# Root application instance for ASGI servers (uvicorn)
app = create_app()
