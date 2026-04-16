import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

def setup_logger(
    name: str = "github-webhook",
    level: Optional[str] = None,
    log_to_file: bool = True,
) -> logging.Logger:
    """
    Production-ready logger with:
    - Console output (Cloud Run / terminal)
    - Optional file logging (local/debug/audit)
    """

    env = os.getenv("ENV", "development").lower()

    # ----------------------------
    # Log level
    # ----------------------------
    if level:
        log_level = getattr(logging, level.upper(), logging.INFO)
    else:
        log_level = logging.DEBUG if env == "development" else logging.INFO

    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # ----------------------------
    # Console Handler (Cloud Run)
    # ----------------------------
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # ----------------------------
    # File Handler (optional)
    # ----------------------------
    if log_to_file:

        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        log_file = log_dir / f"{name}-{datetime.utcnow().date()}.log"

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)

    logger.propagate = False

    logger.info(
        "Logger initialized | env=%s | file_logging=%s",
        env,
        log_to_file,
    )

    return logger