from __future__ import annotations

import hashlib
import hmac
import json
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request, status

from agent.orchestrator import review_pull_request
from api.schemas.common import WebhookAccepted
from config import get_settings
from src.core.exceptions import WebhookSignatureError

router = APIRouter(prefix="/webhook", tags=["webhook"])


@router.post(
    "",
    response_model=WebhookAccepted,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Receive a GitHub webhook",
)
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    delivery_id: Annotated[str | None, Header(alias="X-GitHub-Delivery")] = None,
    event: Annotated[str | None, Header(alias="X-GitHub-Event")] = None,
    signature: Annotated[str | None, Header(alias="X-Hub-Signature-256")] = None,
) -> WebhookAccepted:
    payload = await request.body()
    if len(payload) > get_settings().MAX_BODY_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Payload too large",
        )

    # GitHub always sends this header. For local development only, generate a
    # stable-per-request ID so manually posted payloads can be exercised.
    if not delivery_id and not get_settings().is_production:
        delivery_id = f"local-{uuid4()}"
    elif not delivery_id:
        raise WebhookSignatureError(
            "Missing X-GitHub-Delivery header; verify the request is coming from GitHub"
        )
    if not event:
        raise WebhookSignatureError(
            "Missing X-GitHub-Event header; verify the request is coming from GitHub"
        )

    validate_webhook_signature(
        payload,
        signature,
        get_settings().github_webhook_secret,
    )

    if event == "pull_request":
        try:
            event_payload = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc
        if event_payload.get("action") in {"opened", "synchronize", "reopened"}:
            # Keep the webhook response fast. A queue can replace this task in production.
            background_tasks.add_task(review_pull_request, event_payload)

    # Persist delivery_id for deduplication and publish the raw payload to a
    # queue here. Return immediately so GitHub does not retry long processing.
    return WebhookAccepted(delivery_id=delivery_id)


def validate_webhook_signature(
    payload: bytes, signature: str | None, secret: str
) -> None:
    """
    Verify the HMAC SHA-256 signature of a GitHub webhook request.
    """
    if not secret:
        raise WebhookSignatureError(
            "Webhook secret is not configured; set GITHUB_WEBHOOK_SECRET and restart the API"
        )
    if not signature:
        raise WebhookSignatureError(
            "Missing X-Hub-Signature-256 header; check the GitHub webhook configuration"
        )
    if not signature.startswith("sha256="):
        raise WebhookSignatureError(
            "Malformed X-Hub-Signature-256 header; expected format sha256=<hex digest>"
        )

    expected = (
        "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    )
    if not hmac.compare_digest(signature, expected):
        raise WebhookSignatureError(
            "Webhook signature does not match GITHUB_WEBHOOK_SECRET; verify the secret and restart the API"
        )
