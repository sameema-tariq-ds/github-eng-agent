"""LLM tools used by engineering-agent workflows."""

from __future__ import annotations

from typing import Any

from src.llm.ollama_client import call_ollama
from src.llm.review_prompt import build_review_prompt
from src.llm.schemas import ReviewOutput


def generate_pull_request_review(diff: str, pr_info: dict[str, Any]) -> ReviewOutput:
    """Generate and validate a structured review for a pull-request diff."""
    prompt = build_review_prompt(diff, pr_info)
    return call_ollama(prompt)
