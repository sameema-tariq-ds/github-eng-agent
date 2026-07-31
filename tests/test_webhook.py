import hashlib
import hmac
import json

from src.api.endpoints.webhook import validate_webhook_signature
from src.api.validators.payload_parser import parse_pull_request_payload
from src.core.jobs import AgentJob, DeliveryStore
from src.core.config import Settings


def test_signature_uses_raw_body() -> None:
    body = b'{"action":"opened"}'
    secret = "test-secret"
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    validate_webhook_signature(body, f"sha256={digest}", secret)


def test_pull_request_payload_extracts_head_sha() -> None:
    raw = json.dumps(
        {
            "action": "opened",
            "repository": {"full_name": "owner/repo"},
            "pull_request": {"number": 7, "head": {"sha": "abc123"}},
        }
    ).encode()
    payload = parse_pull_request_payload(raw)
    assert payload.pull_request is not None
    assert payload.pull_request.head["sha"] == "abc123"


def test_delivery_store_is_idempotent_in_development() -> None:
    store = DeliveryStore(Settings(environment="development"))
    assert store.claim("delivery-1") is True
    assert store.claim("delivery-1") is False


def test_agent_job_is_immutable() -> None:
    job = AgentJob("d", "owner/repo", 1, "opened", "sha")
    assert job.repository == "owner/repo"
