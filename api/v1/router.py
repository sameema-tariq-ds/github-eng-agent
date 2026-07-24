from __future__ import annotations

from fastapi import APIRouter

from api.v1.endpoints import health, webhook

router = APIRouter()
router.include_router(health.router)
router.include_router(webhook.router)
