"""Route supported webhook events to agent workflows."""

from __future__ import annotations

import logging
from typing import Any

from src.agent.agents import pr_reviewer

logger = logging.getLogger(__name__)


def route_event(event_type: str, payload: dict[str, Any]) -> None:
    """Route a supported GitHub event to its agent workflow."""
    action = payload.get("action")
    logger.info("Event received event_type=%s action=%s", event_type, action)

    if event_type == "pull_request" and action in {"opened", "synchronize", "reopened"}:
        pr_reviewer.review_pull_request(payload)
        return

    logger.debug("Event ignored event_type=%s action=%s", event_type, action)
