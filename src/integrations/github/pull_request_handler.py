"""Backward-compatible imports for the GitHub agent tools."""

from __future__ import annotations

from src.agent.tools.github_client import (
    extract_pull_request,
    fetch_pull_request_diff,
    post_pull_request_review,
)

handle_pull_request = extract_pull_request
fetch_pr_diff = fetch_pull_request_diff
post_pr_review = post_pull_request_review
