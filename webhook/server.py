import hashlib, hmac, json, os
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from agent.tools.pubsub_client import PubSubClient
from observability.logging import setup_logger

from config.settings import settings


logger = setup_logger("github-webhook")

app = FastAPI()
pubsub = PubSubClient(settings.GCP_PROJECT_ID)

# ---------------------------
# Security Layer
# ---------------------------
def verify_signature(payload_body: bytes, secret_token: str, signature_header: str) -> None:
    """Verify GitHub webhook authenticity using HMAC SHA-256."""

    if not signature_header:
        raise HTTPException(status_code=403, detail="x-hub-signature-256 header is missing!")

    hash_object = hmac.new(secret_token.encode('utf-8'), msg=payload_body, digestmod=hashlib.sha256)

    expected_signature = "sha256=" + hash_object.hexdigest()

    print(expected_signature, signature_header)

    if not hmac.compare_digest(expected_signature, signature_header):
        raise HTTPException(status_code=403, detail="Request signatures didn't match!")

# ---------------------------
# Webhook Endpoint
# ---------------------------
@app.post("/webhook/github")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    """Validate GitHub webhook, filter events, and publish valid ones to Pub/Sub."""
    payload_bytes = await request.body()
    headers = request.headers

    event_type = headers.get("X-GitHub-Event", "")
    delivery_id = headers.get("X-GitHub-Delivery")  # important for dedup
    signature_header = headers.get("X-Hub-Signature-256", "")
    secret_token = settings.GITHUB_WEBHOOK_SECRET

    print('LENGTH OF PAYLOAD BODY',len(payload_bytes))
    print('HASH OF PAYLOAD BODY', hashlib.sha256(payload_bytes).hexdigest())
    print('SECRET TOKEN', (repr(secret_token)))
    print('PAYLOAD BODY', payload_bytes[:200])
    print('SIGNATURE HEADER', signature_header)
    print('EVENT TYPE', event_type)
    print('DELIVERY ID', delivery_id)
    
    # 1. Security check (HMAC)
    if not verify_signature(payload_bytes, secret_token, signature_header):
        logger.warning("Invalid signature detected")
        raise HTTPException(status_code=401, detail="Invalid signature")

    # 2. Parse payload safely
    try:
        payload = json.loads(payload_bytes)
    except json.JSONDecodeError:
        logger.warning("Invalid Json payload")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # 3. Event filtering
    if event_type not in settings.ALLOWED_EVENTS:
        logger.info(f"Ignored event: {event_type}")
        return {
        "status": "ignored",
        "event_type": event_type,
        "delivery_id": delivery_id
    }
    
    # 4. Build message
    message = json.dumps({"event_type": event_type, "payload": payload}).encode()
    # 5. Async publish (non-blocking)
    background_tasks.add_task(pubsub.publish, "github-events", message)
    logger.info(f"Accepted event: {event_type} ({delivery_id})")

    # 6. Response
    return {
        "status": "accepted",
        "event_type": event_type,
        "delivery_id": delivery_id
    }

@app.get("/health")
async def health():
    """Return service health status for monitoring and readiness checks."""
    return {"status": "ok"}