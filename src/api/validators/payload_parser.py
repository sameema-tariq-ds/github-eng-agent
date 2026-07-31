from __future__ import annotations

import json
import logging

from fastapi import HTTPException, status
from pydantic import ValidationError

from src.api.schemas import PullRequestWebhookPayload

logger = logging.getLogger(__name__)


def parse_pull_request_payload(raw_body: bytes) -> PullRequestWebhookPayload:
    """Parse and validate a GitHub pull_request webhook body. Raises
    HTTPException on malformed JSON or schema mismatch."""
    try:
        parsed = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Malformed JSON body"
        ) from exc

    try:
        return PullRequestWebhookPayload.model_validate(parsed)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unexpected payload shape: {exc.errors()}",
        ) from exc
