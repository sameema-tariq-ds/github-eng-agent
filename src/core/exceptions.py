from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response

logger = logging.getLogger(__name__)
ExceptionHandler = Callable[[Request, Exception], Awaitable[Response] | Response]


class AppError(Exception):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error = "internal_error"

    def __init__(self, detail: str = "An unexpected error occurred") -> None:
        super().__init__(detail)
        self.detail = detail


class WebhookSignatureError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    error = "invalid_webhook_signature"


class GitHubAPIError(AppError):
    status_code = status.HTTP_502_BAD_GATEWAY
    error = "github_api_error"


class AgentExecutionError(AppError):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error = "agent_execution_error"


class PubSubError(AppError):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    error = "pubsub_error"


class ConfigurationError(AppError):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error = "configuration_error"


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def _error_response(request: Request, status_code: int, error: str, detail: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": error, "detail": detail, "request_id": _request_id(request)},
    )


async def app_error_handler(request: Request, exc: AppError) -> Response:
    return _error_response(request, exc.status_code, exc.error, exc.detail)


async def http_error_handler(request: Request, exc: HTTPException) -> Response:
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return _error_response(request, exc.status_code, "http_error", detail)


async def validation_error_handler(request: Request, exc: RequestValidationError) -> Response:
    return _error_response(request, status.HTTP_422_UNPROCESSABLE_ENTITY, "validation_error", str(exc.errors()))


async def unhandled_error_handler(request: Request, exc: Exception) -> Response:
    logger.exception("Unhandled application error", exc_info=exc)
    return _error_response(
        request,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "internal_error",
        "An unexpected error occurred",
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(HTTPException, http_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)
