"""Version 1 API endpoint routers."""

from api.v1.endpoints.health import router as health_router
from api.v1.endpoints.webhook import router as webhook_router

__all__ = ["health_router", "webhook_router"]
