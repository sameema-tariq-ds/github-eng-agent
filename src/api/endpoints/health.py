from __future__ import annotations

import time
import httpx
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException

from fastapi import HTTPException

from src.api.schemas import HealthStatus, ServiceStatus
from src.core.config import get_settings

router = APIRouter(prefix="/health", tags=["health"])
_START_TIME = time.monotonic()


def _status() -> HealthStatus:
    """Build the current service health response."""
    settings = get_settings()
    return HealthStatus(
        status=ServiceStatus.OK,
        timestamp=datetime.now(UTC),
        uptime_seconds=round(time.monotonic() - _START_TIME, 2),
        version=settings.app_version,
    )


@router.get("", response_model=HealthStatus, summary="Service health")
async def health_check() -> HealthStatus:
    """Return the service health status."""
    return _status()


@router.get("/live", response_model=HealthStatus, include_in_schema=False)
async def liveness_check() -> HealthStatus:
    """Return the process liveness status."""
    return _status()


@router.get("/ready", response_model=HealthStatus, include_in_schema=False)
async def readiness_check() -> HealthStatus:
    """Return the service readiness status."""
    # Add external dependency checks here once their clients are registered.
    settings = get_settings()
    checks = {}

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{settings.ollama_base_url}/api/tags")
            checks["ollama"] = resp.status_code == 200
    except Exception:
        checks["ollama"] = False

    if not all(checks.values()):
        raise HTTPException(status_code=503, detail=checks)

    return _status()
