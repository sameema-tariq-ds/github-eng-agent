from __future__ import annotations

import logging

from src.api.schemas import PullRequestWebhookPayload
from src.api.validators.event_filters import should_process_pull_request
from src.api.validators.payload_parser import parse_pull_request_payload
from src.core.config import Settings

logger = logging.getLogger(__name__)


def process_webhook_event(
    *,
    event: str,
    raw_body: bytes,
    delivery_id: str,
    settings: Settings,
) -> PullRequestWebhookPayload | None:
    """Validate and process a supported GitHub webhook event.

    Currently only pull request events are supported. Unsupported events,
    unsupported actions, closed PRs, or events from repos/installations
    outside the configured allowlists are ignored.
    """
    if event != "pull_request":
        logger.info(
            "Ignoring unsupported GitHub event '%s' (delivery_id=%s).",
            event,
            delivery_id,
        )
        return None

    payload = parse_pull_request_payload(raw_body)

    if not should_process_pull_request(
        event=event,
        payload=payload,
        settings=settings,
        delivery_id=delivery_id,
    ):
        return None

    return payload
