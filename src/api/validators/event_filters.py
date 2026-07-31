from __future__ import annotations

import logging

from fastapi import HTTPException, status

from src.api.schemas import PullRequestWebhookPayload
from src.core.config import Settings

logger = logging.getLogger(__name__)


def _is_repository_allowed(payload: PullRequestWebhookPayload, settings: Settings) -> bool:
    """Return True if repo allowlisting is unconfigured, or the repo is on it.

    Reads settings.allowed_repositories (tuple[str, ...], expected as
    "owner/name" full names). If the field isn't present on Settings, or is
    empty, no restriction is applied.
    """
    allowed = getattr(settings, "allowed_repositories", ())
    if not allowed:
        return True

    repository = getattr(payload, "repository", None)
    full_name = getattr(repository, "full_name", None)
    return full_name in allowed


def _is_installation_allowed(payload: PullRequestWebhookPayload, settings: Settings) -> bool:
    """Return True if installation restriction is unconfigured, or matches.

    Reads settings.allowed_installation_ids (tuple[int, ...]). If the field
    isn't present on Settings, or is empty, no restriction is applied.
    Currently a no-op: PullRequestWebhookPayload has no `installation` field.
    Only meaningful for GitHub App installations, where the payload includes
    an `installation` object — add it to the schema first if you need this.
    """
    allowed = getattr(settings, "allowed_installation_ids", ())
    if not allowed:
        return True

    installation = getattr(payload, "installation", None)
    installation_id = getattr(installation, "id", None)
    return installation_id in allowed


def _is_pull_request_open(payload: PullRequestWebhookPayload) -> bool:
    """Return True if the PR is open, or the payload doesn't expose state.

    GitHub's `pull_request.state` field is "open" or "closed". Currently a
    no-op: `PullRequestRef` only has `number`, no `state` — add it to the
    schema first if you need this enforced.
    """
    pull_request = getattr(payload, "pull_request", None)
    state = getattr(pull_request, "state", None)
    if state is None:
        return True
    return state == "open"


def should_process_pull_request(
    event: str, payload: PullRequestWebhookPayload, settings: Settings, delivery_id: str
) -> bool:
    """Return whether this webhook event/action should trigger the agent,
    logging (and implicitly accepting) anything that should be skipped."""
    if event != "pull_request":
        logger.info("Ignoring event type=%s delivery_id=%s", event, delivery_id)
        return False

    if payload.action not in settings.supported_pull_request_actions:
        logger.info("Ignoring PR action=%s delivery_id=%s", payload.action, delivery_id)
        return False

    if payload.pull_request is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="pull_request field missing for pull_request event",
        )

    if not _is_pull_request_open(payload):
        logger.info("Ignoring PR that is no longer open delivery_id=%s", delivery_id)
        return False

    if not _is_repository_allowed(payload, settings):
        repo_name = getattr(getattr(payload, "repository", None), "full_name", None)
        logger.info(
            "Ignoring event for repository '%s' not in allowlist delivery_id=%s",
            repo_name,
            delivery_id,
        )
        return False

    if not _is_installation_allowed(payload, settings):
        installation_id = getattr(getattr(payload, "installation", None), "id", None)
        logger.info(
            "Ignoring event for installation '%s' not in allowlist delivery_id=%s",
            installation_id,
            delivery_id,
        )
        return False

    return True
