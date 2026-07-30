# api\main.py
from __future__ import annotations

import os

from config.logging_config import configure_logging
from config.settings import get_settings
from src.core.app import create_app

configure_logging()

app = create_app()

if __name__ == "__main__":
    import uvicorn

    settings = get_settings()

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    )
