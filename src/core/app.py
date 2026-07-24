from __future__ import annotations

from fastapi import FastAPI

from config.settings import get_settings
from src.core.exceptions import register_exception_handlers
from src.core.lifespan import lifespan
from src.core.middleware import register_middleware


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "AI-powered GitHub engineering agent built with LangGraph. "
            "Processes GitHub webhook events, analyzes repositories and pull requests, "
            "and automates engineering workflows."
        ),
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None if settings.is_production else "/redoc",
        lifespan=lifespan,
    )

    register_middleware(app)
    register_exception_handlers(app)

    from api.v1.router import router as v1_router

    app.include_router(v1_router, prefix="/v1")
    return app
