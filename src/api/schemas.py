from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ServiceStatus(StrEnum):
    """API health indicator."""

    OK = "ok"
    DEGRADED = "degraded"
    UP = "up"


class HealthStatus(BaseModel):
    """Response model for GET /v1/health."""

    status: ServiceStatus
    timestamp: datetime
    uptime_seconds: float
    version: str

    model_config = ConfigDict(use_enum_values=True)


class WebhookAccepted(BaseModel):
    received: bool = True
    delivery_id: str


class ErrorDetail(BaseModel):
    """Standard error payload returned on 4xx / 5xx responses."""

    error: str
    detail: str | None = None
    request_id: str | None = None


class PullRequestRef(BaseModel):
    number: int
    state: str = "open"
    # GitHub's head object contains nested ``user`` and ``repo`` objects;
    # only ``sha`` is consumed by the agent.
    head: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="ignore")


class RepositoryRef(BaseModel):
    full_name: str

    model_config = ConfigDict(extra="ignore")


class PullRequestWebhookPayload(BaseModel):
    action: str
    repository: RepositoryRef
    pull_request: PullRequestRef | None = None
    installation: dict[str, Any] | None = None
