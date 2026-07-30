from __future__ import annotations

import json
from typing import Any

from fastapi import BackgroundTasks

from config.settings import get_settings
from src.agent.agents.pr_reviewer import review_pull_request
from src.core.exceptions import InvalidWebhookPayloadError


def dispatch_event(
    event: str,
    payload: bytes,
    background_tasks: BackgroundTasks,
) -> None:
    """Validate a webhook payload and queue supported pull-request reviews."""
    if event != "pull_request":
        return

    try:
        event_payload: dict[str, Any] = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise InvalidWebhookPayloadError from exc

    if not isinstance(event_payload, dict):
        raise InvalidWebhookPayloadError

    if event_payload.get("action") in get_settings().supported_pull_request_actions:
        background_tasks.add_task(review_pull_request, event_payload)
