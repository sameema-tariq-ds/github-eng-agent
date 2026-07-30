from __future__ import annotations

import functools
import os
from collections.abc import Callable
from typing import cast


def _env() -> str:
    """Read ENV without importing Settings to avoid circular imports."""
    return os.environ.get("APP_ENV", "development").lower()


# ---------------------------------------------------------------------------
# Boolean helpers
# ---------------------------------------------------------------------------


def is_production() -> bool:
    """Return whether the configured environment is production."""
    return _env() == "production"


def is_development() -> bool:
    """Return whether the configured environment is development."""
    return _env() == "development"


def is_test() -> bool:
    """Return whether the configured environment is test."""
    return _env() == "test"


def is_staging() -> bool:
    """Return whether the configured environment is staging."""
    return _env() == "staging"


# ---------------------------------------------------------------------------
# Decorators
# ---------------------------------------------------------------------------


def require_production[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    """Decorate a function so it can run only in production."""

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        """Invoke the wrapped function when production is enabled."""
        if not is_production():
            raise RuntimeError(
                f"{func.__qualname__} must only be called in production "
                f"(current ENV={_env()!r})."
            )
        return func(*args, **kwargs)

    return wrapper


def require_not_production[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    """Decorate a function so it is blocked in production."""

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        """Invoke the wrapped function outside production."""
        if is_production():
            raise RuntimeError(
                f"{func.__qualname__} must NOT be called in production "
                f"(current ENV={_env()!r}). This operation is too destructive."
            )
        return func(*args, **kwargs)

    return wrapper


def development_only[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    """Decorate a function so it executes only in development."""

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        """Invoke the wrapped function only in development."""
        if is_development():
            return func(*args, **kwargs)
        return cast(R, None)

    return wrapper


# ---------------------------------------------------------------------------
# Guard function for destructive operations
# ---------------------------------------------------------------------------


def guard_destructive(operation_name: str, *, allow_in_test: bool = True) -> None:
    """Log or reject destructive operations according to the current environment."""
    """
    Call before any operation that modifies data (commits, deletes, merges).

    - In development: logs a warning but allows the operation.
    - In test: allows if allow_in_test=True (default), raises if False.
    - In production: always allows (this is the live system — the
      human-approval gate in the agent is the safety mechanism there).

    This function is a documentation + dev-time reminder tool.
    It is NOT a security boundary.

    Example
    -------
        guard_destructive("commit fix to branch agent-fix/abc123")
        commit_fix_to_branch(...)
    """
    env = _env()

    if env == "test" and not allow_in_test:
        raise RuntimeError(
            f"Destructive operation blocked in test: {operation_name!r}. "
            "Pass allow_in_test=True if this test genuinely needs to run it."
        )

    if env == "development":
        # Import here to avoid circular dependency with logging module
        import logging

        logging.getLogger("config.environment").warning(
            "Destructive operation in development: %r — proceeding.", operation_name
        )


# ---------------------------------------------------------------------------
# Startup environment report (printed once at boot, dev only)
# ---------------------------------------------------------------------------


@development_only
def print_env_summary() -> None:
    """Print a non-sensitive development configuration summary."""
    """
    Prints a human-readable summary of key config values at startup.
    Only runs in development. Never prints secrets.

    Call from your application entry point:
        from config.environment import print_env_summary
        print_env_summary()
    """
    from config.settings import get_settings

    s = get_settings()

    lines = [
        "",
        "  eng-agent — development mode",
        f"  ENV              : {s.environment}",
        f"  Webhook host     : {s.host}",
        f"  Webhook port     : {s.port}",
        f"  LLM model        : {s.ollama_model}",
        f"  Review publishing: {s.github_post_review}",
        "",
        "  Secrets: github_token=***, webhook_secret=***",
        "",
    ]
    print("\n".join(lines))
