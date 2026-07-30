"""GitHub tools available to engineering-agent workflows."""

from __future__ import annotations

from typing import Any

import logging
import requests

from config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def extract_pull_request(payload: dict[str, Any]) -> dict[str, Any]:
    """Extract the GitHub fields required by the pull-request reviewer."""
    pull_request = payload.get("pull_request") or {}
    repository = payload.get("repository") or {}
    pull_url = pull_request.get("url", "").rstrip("/")

    return {
        "repo_full_name": repository.get("full_name", ""),
        "pr_number": pull_request.get("number", 0),
        "head_sha": (pull_request.get("head") or {}).get("sha", ""),
        "diff_url": pull_request.get("diff_url", ""),
        "changed_files": pull_request.get("changed_files", 0),
        "pull_url": pull_url,
        "review_url": f"{pull_url}/reviews" if pull_url else "",
    }


def _github_headers(accept: str = "application/vnd.github+json") -> dict[str, str]:
    """Build authenticated headers for GitHub API requests."""
    return {
        "Accept": accept, 
        "Authorization": f"Bearer {settings.github_token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def fetch_pull_request_diff(pr_info: dict[str, Any]) -> str:
    """
    Fetch a pull-request diff from GitHub. It tells about
        1. content in the file before (a/) the change and after (/b) the change.
        2. is file exists before os is being created now?
    """
    response = requests.get(
        pr_info["pull_url"],
        headers=_github_headers("application/vnd.github.diff"),
        timeout=30,
    )
    response.raise_for_status()
    return response.text


def post_pull_request_review(pr_info: dict[str, Any], review: dict[str, Any]) -> None:
    """Post a review, including valid line comments, to GitHub."""
    if not pr_info.get("review_url"):
        raise ValueError("Missing pull-request review URL")

    comments = []
    for issue in review.get("issues", []):
        if not all(issue.get(field) for field in ("file", "line", "comment")):
            continue
        comments.append(
            {
                "path": issue["file"],
                "line": issue["line"],
                "side": issue.get("side", "RIGHT"),
                "body": issue["comment"],
            }
        )

    response = requests.post(
        pr_info["review_url"],
        headers=_github_headers(),
        json={
            "commit_id": pr_info["head_sha"],
            "body": review.get("summary", ""),
            "event": "COMMENT",
            "comments": comments,
        },
        timeout=30,
    )
    response.raise_for_status()
