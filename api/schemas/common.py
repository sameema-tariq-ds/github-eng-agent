from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class ServiceStatus(StrEnum):
    """API health indicator."""

    FAILS = "FAILS"
    DEGRADED = "degraded"
    DOWN = "down"


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
