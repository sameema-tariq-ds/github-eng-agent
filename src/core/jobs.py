"""Durable webhook delivery tracking and job publishing."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from threading import Lock
from typing import Any

from src.core.config import Settings
from src.core.exceptions import PubSubError

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class AgentJob:
    delivery_id: str
    repository: str
    pull_request_number: int
    action: str
    commit_sha: str


class DeliveryStore:
    """Firestore-backed idempotency store, with an explicit dev-only memory mode."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._memory: set[str] = set()
        self._lock = Lock()
        self._client: Any = None
        if settings.is_production:
            if not settings.firestore_collection:
                raise RuntimeError("FIRESTORE_COLLECTION is required in production")
            try:
                from google.cloud import firestore
                self._client = firestore.Client()
            except Exception as exc:
                raise RuntimeError("Firestore is required in production") from exc

    def claim(self, delivery_id: str) -> bool:
        """Atomically claim a delivery; false means it was already accepted."""
        if self._client is not None:
            ref = self._client.collection(self.settings.firestore_collection).document(
                delivery_id
            )

            @self._client.transactional
            def _claim(transaction: Any) -> bool:
                snapshot = ref.get(transaction=transaction)
                if snapshot.exists:
                    return False
                transaction.create(
                    ref,
                    {"status": "queued", "created_at": datetime.now(UTC)},
                )
                return True

            return _claim(self._client.transaction())

        with self._lock:
            if delivery_id in self._memory:
                return False
            self._memory.add(delivery_id)
            return True

    def release(self, delivery_id: str) -> None:
        """Release a failed claim so a later webhook retry can be processed."""
        if self._client is not None:
            self._client.collection(self.settings.firestore_collection).document(
                delivery_id
            ).delete()
            return
        with self._lock:
            self._memory.discard(delivery_id)


class JobQueue:
    """Publish jobs to Pub/Sub; permit in-process fallback only outside production."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._publisher: Any = None
        self._topic_path: str | None = None
        if settings.pubsub_topic:
            try:
                from google.cloud import pubsub_v1

                self._publisher = pubsub_v1.PublisherClient()
                project = os.getenv("GOOGLE_CLOUD_PROJECT", "")
                if settings.pubsub_topic.startswith("projects/"):
                    self._topic_path = settings.pubsub_topic
                elif project:
                    self._topic_path = self._publisher.topic_path(
                        project, settings.pubsub_topic
                    )
                else:
                    raise RuntimeError(
                        "PUBSUB_TOPIC must be a full topic path or GOOGLE_CLOUD_PROJECT must be set"
                    )
            except Exception as exc:
                raise RuntimeError("Unable to initialize Pub/Sub publisher") from exc
        elif settings.is_production:
            raise RuntimeError("PUBSUB_TOPIC is required in production")

    def publish(self, job: AgentJob) -> None:
        if self._publisher is None or self._topic_path is None:
            logger.warning("Using non-durable in-process job execution delivery_id=%s", job.delivery_id)
            return
        try:
            future = self._publisher.publish(
                self._topic_path,
                json.dumps(asdict(job)).encode("utf-8"),
                delivery_id=job.delivery_id,
            )
            future.result(timeout=10)
        except Exception as exc:
            raise PubSubError("Failed to publish agent job") from exc
