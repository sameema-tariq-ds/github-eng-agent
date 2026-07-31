from __future__ import annotations

from fastapi import APIRouter

from src.api.endpoints import health, webhook

router = APIRouter()
router.include_router(health.router)
router.include_router(webhook.router)
