"""
config/environment.py — Environment guards and helpers.

Import these instead of checking `settings.env == "production"` directly.
They make intent clear at call sites and are easy to mock in tests.

Usage
-----
    from config.environment import require_production, guard_destructive

    @require_not_production          # raises in prod
    def drop_all_firestore_docs(): ...

    guard_destructive("delete branch")  # logs a warning in dev, raises in prod
                                        # unless explicitly confirmed
"""

from __future__ import annotations

import functools
import os
from typing import Callable, TypeVar

F = TypeVar("F", bound=Callable)


def _env() -> str:
    """Read ENV without importing Settings to avoid circular imports."""
    return os.environ.get("ENV", "development").lower()


# ---------------------------------------------------------------------------
# Boolean helpers
# ---------------------------------------------------------------------------

def is_production() -> bool:
    return _env() == "production"


def is_development() -> bool:
    return _env() == "development"


def is_test() -> bool:
    return _env() == "test"


def is_staging() -> bool:
    return _env() == "staging"


# ---------------------------------------------------------------------------
# Decorators
# ---------------------------------------------------------------------------

def require_production(func: F) -> F:
    """
    Decorator: raises RuntimeError if called outside production.
    Use for functions that should only run in prod (e.g. real Pub/Sub publish).
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not is_production():
            raise RuntimeError(
                f"{func.__qualname__} must only be called in production "
                f"(current ENV={_env()!r})."
            )
        return func(*args, **kwargs)
    return wrapper  # type: ignore[return-value]


def require_not_production(func: F) -> F:
    """
    Decorator: raises RuntimeError if called in production.
    Use for dangerous utility functions (seed data, bulk deletes, etc.).
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if is_production():
            raise RuntimeError(
                f"{func.__qualname__} must NOT be called in production "
                f"(current ENV={_env()!r}). This operation is too destructive."
            )
        return func(*args, **kwargs)
    return wrapper  # type: ignore[return-value]


def development_only(func: F) -> F:
    """
    Decorator: no-ops silently if not in development.
    Use for dev-only helpers like printing debug state.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if is_development():
            return func(*args, **kwargs)
    return wrapper  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Guard function for destructive operations
# ---------------------------------------------------------------------------

def guard_destructive(operation_name: str, *, allow_in_test: bool = True) -> None:
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
        f"  ENV              : {s.env}",
        f"  GCP project      : {s.gcp_project_id}",
        f"  GCP region       : {s.gcp_region}",
        f"  Pub/Sub topic    : {s.pubsub_topic_github_events}",
        f"  Firestore coll.  : {s.firestore_collection_state}",
        f"  LLM (reviewer)   : {s.llm_model_pr_reviewer}",
        f"  LLM (fix-gen)    : {s.llm_model_fix_generator}",
        f"  Human approval   : {s.agent_require_human_approval}",
        f"  Rate limit/repo  : {s.agent_rate_limit_per_repo_per_hour}/hr",
        f"  Webhook port     : {s.webhook_port}",
        "",
        "  Secrets: github_token=***, openrouter_api_key=***, webhook_secret=***",
        "",
    ]
    print("\n".join(lines))