from __future__ import annotations

import json
import logging
import os
import re
import sys
from datetime import UTC, datetime

_REDACT_PATTERNS = [
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),          # GitHub PAT/App tokens
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9\-\._~\+/]+=*", re.IGNORECASE),
    re.compile(r"(?i)(authorization|x-hub-signature-256)\"?\s*[:=]\s*\"?[^\s\"]+"),
]


def _redact(text: str) -> str:
    for pattern in _REDACT_PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    return text


class RedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = _redact(str(record.msg))
        if record.args:
            record.args = tuple(
                _redact(str(a)) if isinstance(a, str) else a for a in record.args
            )
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "file": record.filename,
            "line": record.lineno,
        }
        # Pull through structured `extra=` fields without leaking internal
        # LogRecord attributes.
        reserved = set(vars(logging.makeLogRecord({})).keys()) | {"message", "asctime"}
        for key, value in vars(record).items():
            if key not in reserved and key not in payload:
                payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def configure_logging(level: int | str = logging.INFO) -> None:
    """Configure application logging once at process startup. stdout only."""
    env_level = os.getenv("LOG_LEVEL")
    if env_level:
        level = env_level.upper()

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    if root_logger.handlers:
        return  # already configured — avoid duplicate handlers on reload

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(JsonFormatter())
    handler.addFilter(RedactingFilter())
    handler.setLevel(level)

    root_logger.addHandler(handler)

    # Quiet noisy third-party loggers unless explicitly debugging.
    resolved_level = logging.getLevelName(level) if isinstance(level, str) else level
    if resolved_level > logging.DEBUG:
        for noisy in ("httpx", "httpcore", "uvicorn.access"):
            logging.getLogger(noisy).setLevel(logging.WARNING)