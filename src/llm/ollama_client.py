"""LangChain client for a local Ollama model."""

from __future__ import annotations

import logging
import time
from typing import Any

from tenacity import (
    RetryCallState,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from config.settings import get_settings
from src.core.exceptions import LLMClientError
from src.llm.schemas import ReviewOutput

logger = logging.getLogger(__name__)
settings = get_settings()


def _log_retry(retry_state: RetryCallState) -> None:
    """Log the next Ollama retry attempt without exposing request content."""
    exception_name = "unknown"
    if retry_state.outcome is not None and retry_state.outcome.failed:
        exception = retry_state.outcome.exception()
        exception_name = type(exception).__name__ if exception else "unknown"
    logger.warning(
        "Ollama request retrying attempt=%s model=%s error_type=%s",
        retry_state.attempt_number + 1,
        settings.ollama_model,
        exception_name,
    )


def _build_client() -> Any:
    """Construct the configured structured-output Ollama client."""
    try:
        from langchain_ollama import ChatOllama
    except ImportError as exc:
        raise LLMClientError(
            "langchain-ollama is not installed; install the project dependencies"
        ) from exc

    logger.debug(
        "Initializing Ollama client model=%s base_url=%s",
        settings.ollama_model,
        settings.ollama_base_url,
    )

    return ChatOllama(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
        temperature=settings.temperature,
        num_predict=settings.max_tokens,
        client_kwargs={"timeout": settings.ollama_timeout},
    )


def call_ollama(prompt: str) -> ReviewOutput:
    """Call Ollama and validate the response against ``ReviewOutput``."""
    started_at = time.perf_counter()
    logger.info(
        "LLM review started provider=ollama model=%s prompt_chars=%s",
        settings.ollama_model,
        len(prompt),
    )

    try:
        review = _call_ollama_with_retry(prompt)
        elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)
        logger.info(
            "LLM review completed provider=ollama model=%s issues=%s duration_ms=%s",
            settings.ollama_model,
            len(review.issues),
            elapsed_ms,
        )
        return review
    except LLMClientError as exc:
        logger.error(
            "LLM review failed provider=ollama model=%s error_type=%s",
            settings.ollama_model,
            type(exc).__name__,
        )
        raise
    except Exception as exc:
        elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)
        logger.exception(
            "LLM review failed provider=ollama model=%s duration_ms=%s",
            settings.ollama_model,
            elapsed_ms,
        )
        raise LLMClientError("Ollama review generation failed") from exc


@retry(
    retry=retry_if_exception_type((TimeoutError, ConnectionError)),
    stop=stop_after_attempt(settings.ollama_max_attempts),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    before_sleep=_log_retry,
    reraise=True,
)
def _call_ollama_with_retry(prompt: str) -> ReviewOutput:
    """Call Ollama and validate the response against ``ReviewOutput``."""
    structured_client = _build_client().with_structured_output(
        ReviewOutput,
        method="json_schema",
    )

    result: Any = structured_client.invoke(prompt)

    if isinstance(result, ReviewOutput):
        return result
    return ReviewOutput.model_validate(result)
