# api\main.py
from __future__ import annotations


from src.core.logging import configure_logging
from src.core.config import get_settings
from src.api.app import create_app

configure_logging()

app = create_app()

if __name__ == "__main__":
    import uvicorn

    settings = get_settings()

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=not settings.is_production,
    )
