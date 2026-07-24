from __future__ import annotations

import logging
import os

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "app.log")

# Full format: timestamp | level | filename:lineno | module path | message
LOG_FORMAT = (
    "%(asctime)s | %(levelname)s | %(filename)s:%(lineno)d | %(name)s | %(message)s"
)
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------


def configure_logging(level: int | str = logging.INFO) -> None:
    """Call once at application startup to configure all handlers.

    Args:
        level: Root log level. Accepts logging.INFO, logging.DEBUG, or
               their string equivalents ("INFO", "DEBUG", etc.).
               Defaults to INFO. Override via the LOG_LEVEL env var.
    """
    # Allow env-var override so staging/prod can dial up DEBUG without code changes
    env_level = os.getenv("LOG_LEVEL")
    if env_level:
        level = env_level.upper()

    os.makedirs(LOG_DIR, exist_ok=True)

    formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)

    # --- File handler ---
    # A plain FileHandler is safer under Uvicorn's multi-process/reload mode.
    # RotatingFileHandler can collide when more than one process tries to roll
    # the same file at once.
    file_handler = logging.FileHandler(
        filename=LOG_FILE,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)

    # --- Console (stdout) handler ---
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)

    # --- Root logger ---
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Avoid duplicate handlers if configure_logging() is called more than once
    if not root_logger.handlers:
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
