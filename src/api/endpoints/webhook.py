from __future__ import annotations

import hashlib
import hmac
import logging
from functools import lru_cache
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request, status

from src.api.schemas import WebhookAccepted
from src.core.config import get_settings
from src.core.exceptions import WebhookSignatureError
from src.core.jobs import AgentJob, DeliveryStore, JobQueue
from src.agent.graph import run as run_agent
from src.api.validators.github_webhook import process_webhook_event


router = APIRouter(prefix="/webhook", tags=["webhook"])
logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _delivery_store() -> DeliveryStore:
    return DeliveryStore(get_settings())


@lru_cache(maxsize=1)
def _job_queue() -> JobQueue:
    return JobQueue(get_settings())


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
    """Authenticate, validate, and asynchronously queue a GitHub webhook."""
    raw_body = await request.body()
    if len(raw_body) > get_settings().MAX_BODY_BYTES:
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
        raw_body,
        signature,
        get_settings().github_webhook_secret,
    )


    # run pull_review event
    payload = process_webhook_event(
        event=event,
        raw_body=raw_body,
        delivery_id=delivery_id,
        settings=get_settings(),
    )

    if payload is None:
        return WebhookAccepted(delivery_id=delivery_id)

    if not _delivery_store().claim(delivery_id):
        logger.info("Ignoring duplicate GitHub delivery_id=%s", delivery_id)
        return WebhookAccepted(delivery_id=delivery_id)

    if payload.pull_request is None:
        raise HTTPException(status_code=422, detail="Missing pull request data")
    commit_sha = payload.pull_request.head.get("sha", "")
    if not commit_sha:
        raise HTTPException(status_code=422, detail="Missing pull request head SHA")

    job = AgentJob(
        delivery_id=delivery_id,
        repository=payload.repository.full_name,
        pull_request_number=payload.pull_request.number,
        action=payload.action,
        commit_sha=commit_sha,
    )
    try:
        _job_queue().publish(job)
    except Exception:
        _delivery_store().release(delivery_id)
        raise

    # Local development fallback only. Production always publishes to Pub/Sub.
    if not get_settings().pubsub_topic:
        background_tasks.add_task(
            run_agent,
            repository=job.repository,
            pull_request_number=job.pull_request_number,
            delivery_id=job.delivery_id,
            commit_sha=job.commit_sha,
            action=job.action,
        )


    return WebhookAccepted(delivery_id=delivery_id)


def validate_webhook_signature(
    payload: bytes, signature: str | None, secret: str
) -> None:
    """Verify the HMAC SHA-256 signature of a GitHub webhook request."""
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
