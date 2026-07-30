from __future__ import annotations

import logging
import os
import sys

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "app.log")

# Full format: timestamp | level | filename:lineno | module path | message
LOG_FORMAT = (
    "%(asctime)s | %(levelname)s | %(filename)s:%(lineno)d | %(name)s | %(message)s"
)
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def configure_logging(level: int | str = logging.INFO) -> None:
    """Configure application logging handlers once at process startup."""
    # Allow env-var override so staging/prod can dial up DEBUG without code changes
    env_level = os.getenv("LOG_LEVEL")
    if env_level:
        level = env_level.upper()

    os.makedirs(LOG_DIR, exist_ok=True)

    formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)

    # --- Console (stdout) handler ---
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)

    # --- Root logger ---
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Avoid duplicate handlers if configure_logging() is called more than once
    if not root_logger.handlers:
        reload_mode = "--reload" in sys.argv or os.getenv(
            "UVICORN_RELOAD", ""
        ).lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        if not reload_mode:
            file_handler = logging.FileHandler(filename=LOG_FILE, encoding="utf-8")
            file_handler.setFormatter(formatter)
            file_handler.setLevel(level)
            root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
