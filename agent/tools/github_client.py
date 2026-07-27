"""GitHub REST calls used by the PR reviewer."""

from __future__ import annotations

from typing import Any

import httpx

from agent.models import ChangedFile, PullRequestRef


class GitHubClient:
    def __init__(self, token: str, *, api_url: str = "https://api.github.com") -> None:
        self.api_url = api_url.rstrip("/")
        self.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def _get(self, path: str, **params: Any) -> Any:
        response = httpx.get(
            f"{self.api_url}{path}", headers=self.headers, params=params, timeout=30
        )
        response.raise_for_status()
        return response.json()

    def get_changed_files(self, pr: PullRequestRef) -> list[ChangedFile]:
        data = self._get(f"/repos/{pr.owner}/{pr.repo}/pulls/{pr.number}/files", per_page=100)
        return [
            ChangedFile(
                filename=item["filename"],
                status=item["status"],
                additions=item.get("additions", 0),
                deletions=item.get("deletions", 0),
                patch=item.get("patch") or "[binary or unavailable patch]",
            )
            for item in data
        ]

    def get_check_summary(self, pr: PullRequestRef) -> dict[str, Any]:
        return self._get(f"/repos/{pr.owner}/{pr.repo}/commits/{pr.sha}/check-runs")

    def post_comment(self, pr: PullRequestRef, body: str) -> None:
        response = httpx.post(
            f"{self.api_url}/repos/{pr.owner}/{pr.repo}/issues/{pr.number}/comments",
            headers=self.headers, json={"body": body}, timeout=30,
        )
        response.raise_for_status()
