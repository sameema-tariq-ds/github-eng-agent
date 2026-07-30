from __future__ import annotations

import logging
import time
from typing import Any

from config.settings import get_settings
from src.agent.tools.github_client import (
    extract_pull_request,
    fetch_pull_request_diff,
    post_pull_request_review,
)
from src.agent.tools.review_generator import generate_pull_request_review

logger = logging.getLogger(__name__)


def review_pull_request(payload: dict[str, Any]) -> None:
    """Fetch, review, and publish one pull-request review."""
    pr_info = extract_pull_request(payload)
    repository = pr_info.get("repo_full_name", "unknown repository")
    pr_number = pr_info.get("pr_number", "unknown")
    started_at = time.perf_counter()

    logger.info("PR review started repository=%s pr=%s", repository, pr_number)

    if not pr_info["pull_url"]:
        logger.warning(
            "PR review skipped reason=malformed_payload repository=%s pr=%s",
            repository,
            pr_number,
        )
        return

    if not get_settings().github_post_review:
        logger.info(
            "PR review generated but publishing is disabled "
            "repository=%s pr=%s set GITHUB_POST_REVIEW=true to enable",
            repository,
            pr_number,
        )
        return

    try:
        logger.info("Fetching PR diff repository=%s pr=%s", repository, pr_number)
        diff = fetch_pull_request_diff(pr_info)
        logger.info(
            "PR diff fetched repository=%s pr=%s diff_chars=%s diff=%s",
            repository,
            pr_number,
            len(diff),
            diff,
        )
    except Exception:
        logger.exception(
            "PR diff fetch failed repository=%s pr=%s",
            repository,
            pr_number,
        )
        return

    try:
        logger.info("Generating PR review repository=%s pr=%s", repository, pr_number)
        review = generate_pull_request_review(diff, pr_info)
    except Exception:
        logger.exception(
            "PR review generation failed repository=%s pr=%s review=%s",
            repository,
            pr_number,
            "unavailable",
        )
        return

    try:
        logger.info(
            "Publishing PR review repository=%s pr=%s review=%s",
            repository,
            pr_number,
            review,
        )
        post_pull_request_review(pr_info, review.model_dump(mode="json"))
        elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)
        logger.info(
            "PR review completed repository=%s pr=%s issues=%s duration_ms=%s",
            repository,
            pr_number,
            len(review.issues),
            elapsed_ms,
        )
    except Exception:
        logger.exception(
            "PR review publish failed repository=%s pr=%s",
            repository,
            pr_number,
        )
