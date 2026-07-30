from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
dotenv_path = BASE_DIR / ".env"
load_dotenv(dotenv_path)


DEFAULT_APP_NAME = "github-engineering-agent"
DEFAULT_APP_VERSION = "1.0.0"
DEFAULT_ENVIRONMENT = "development"
DEFAULT_LOG_LEVEL = "INFO"

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8001

DEFAULT_ALLOWED_ORIGINS: tuple[str, ...] = ()

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "smollm:1.7b"
MAX_TOKENS = 2000
TEMPERATURE = 0.6
OLLAMA_MAX_ATTEMPTS = 3
OLLAMA_TIMEOUT = 300

SUPPORTED_PULL_REQUEST_ACTIONS = (
    "opened",
    "synchronize",
    "reopened",
)

GITHUB_POST_REVIEW = True

def _get_env_int(name: str, default: int) -> int:
    """Read an integer environment variable or return its default."""
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return int(value)


def _get_env_float(name: str, default: float) -> float:
    """Read a floating-point environment variable or return its default."""
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return float(value)


def _get_env_str(name: str, default: str) -> str:
    """Read and normalize a string environment variable."""
    value = os.getenv(name)
    return default if value is None or value.strip() == "" else value.strip()


def _get_env_bool(name: str, default: bool) -> bool:
    """Read a boolean environment variable using conventional true values."""
    value = os.getenv(name)
    if not value or not value.strip():
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def _get_env_list(name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    """Read a comma-separated environment variable as a tuple."""
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default

    return tuple(item.strip() for item in value.split(",") if item.strip())


# ── Settings dataclass ────────────────────────────────────────────────────────
@dataclass(frozen=True, slots=True)
class Settings:
    # App
    app_name: str = DEFAULT_APP_NAME
    app_version: str = DEFAULT_APP_VERSION
    environment: str = DEFAULT_ENVIRONMENT
    log_level: str = DEFAULT_LOG_LEVEL

    # server
    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    allowed_origins: tuple[str, ...] = DEFAULT_ALLOWED_ORIGINS
    max_upload_size_mb: int = 10
    github_webhook_secret: str = ""
    github_token: str = ""
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    github_post_review: bool = GITHUB_POST_REVIEW 


    # ollama
    ollama_base_url: str = OLLAMA_BASE_URL
    ollama_model: str = OLLAMA_MODEL
    max_tokens: int = MAX_TOKENS
    temperature: float = TEMPERATURE
    ollama_max_attempts: int = OLLAMA_MAX_ATTEMPTS
    ollama_timeout: int = OLLAMA_TIMEOUT

    supported_pull_request_actions: tuple[str, ...] = SUPPORTED_PULL_REQUEST_ACTIONS

    # ── Derived properties ────────────────────────────────────────────────────
    @property
    def MAX_BODY_BYTES(self) -> int:  # noqa: N802  (kept for call-site compat)
        """Return the maximum accepted webhook body size in bytes."""
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def APP_NAME(self) -> str:  # noqa: N802
        """Return the configured application name."""
        return self.app_name

    @property
    def APP_VERSION(self) -> str:  # noqa: N802
        """Return the configured application version."""
        return self.app_version

    @property
    def ENV(self) -> str:  # noqa: N802
        """Return the configured deployment environment."""
        return self.environment

    @property
    def is_production(self) -> bool:
        """Return whether the service runs in production mode."""
        return self.environment.lower() == "production"

    @classmethod
    def from_env(cls) -> Settings:
        """Build immutable settings from the process environment."""
        return cls(
            app_name=_get_env_str("APP_NAME", DEFAULT_APP_NAME),
            app_version=_get_env_str("APP_VERSION", DEFAULT_APP_VERSION),
            environment=_get_env_str("APP_ENV", DEFAULT_ENVIRONMENT),
            log_level=_get_env_str("LOG_LEVEL", DEFAULT_LOG_LEVEL).upper(),
            host=_get_env_str("HOST", DEFAULT_HOST),
            port=_get_env_int("PORT", DEFAULT_PORT),
            allowed_origins=_get_env_list("ALLOWED_ORIGINS", DEFAULT_ALLOWED_ORIGINS),
            max_upload_size_mb=_get_env_int("MAX_UPLOAD_SIZE_MB", 10),
            github_webhook_secret=_get_env_str("GITHUB_WEBHOOK_SECRET", ""),
            github_token=_get_env_str("GITHUB_TOKEN", ""),
            openai_api_key=_get_env_str("OPENAI_API_KEY", ""),
            openai_model=_get_env_str("OPENAI_MODEL", "gpt-4o-mini"),
            github_post_review=_get_env_bool("GITHUB_POST_REVIEW", GITHUB_POST_REVIEW),
            ollama_base_url=_get_env_str("OLLAMA_BASE_URL", OLLAMA_BASE_URL),
            ollama_model=_get_env_str("OLLAMA_MODEL", OLLAMA_MODEL),
            max_tokens=_get_env_int("MAX_TOKENS", MAX_TOKENS),
            temperature=_get_env_float("TEMPERATURE", TEMPERATURE),
            ollama_max_attempts=_get_env_int(
                "OLLAMA_MAX_ATTEMPTS", OLLAMA_MAX_ATTEMPTS
            ),
            ollama_timeout=_get_env_int("OLLAMA_TIMEOUT", OLLAMA_TIMEOUT),
            supported_pull_request_actions=_get_env_list(
                "SUPPORTED_PULL_REQUEST_ACTIONS", SUPPORTED_PULL_REQUEST_ACTIONS
            ),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached application settings instance."""
    return Settings.from_env()
