"""Bounded, authenticated GitHub pull-request access."""

from __future__ import annotations

from typing import Any

from github import Auth, Github, GithubException
from langchain_core.tools import tool

from src.core.config import get_settings
from src.core.exceptions import GitHubAPIError, GithubTokenError


def _get_github_client() -> Github:
    token = get_settings().github_token
    if not token:
        raise GithubTokenError("GITHUB_TOKEN is not configured")
    return Github(auth=Auth.Token(token), timeout=15, per_page=100)


def fetch_pull_request(repo: str, pr_number: int) -> dict[str, Any]:
    """Fetch PR metadata and a bounded set of changed-file patches."""
    if not repo or repo.count("/") != 1 or pr_number < 1:
        raise GitHubAPIError("Invalid repository or pull request number")
    try:
        github = _get_github_client()
        pull_request = github.get_repo(repo).get_pull(pr_number)
        files: list[dict[str, Any]] = []
        max_files = 200
        for changed_file in pull_request.get_files():
            files.append(
                {
                    "filename": changed_file.filename,
                    "status": changed_file.status,
                    "patch": changed_file.patch or "",
                    "additions": changed_file.additions,
                    "deletions": changed_file.deletions,
                }
            )
            if len(files) >= max_files:
                break
        return {
            "pr_number": pull_request.number,
            "title": pull_request.title,
            "state": pull_request.state,
            "author": pull_request.user.login if pull_request.user else None,
            "body": pull_request.body or "",
            "url": pull_request.html_url,
            "base_branch": pull_request.base.ref,
            "head_branch": pull_request.head.ref,
            "mergeable": pull_request.mergeable,
            "additions": pull_request.additions,
            "deletions": pull_request.deletions,
            "changed_files": pull_request.changed_files,
            "files": files,
        }
    except GithubException as exc:
        data = exc.data if isinstance(exc.data, dict) else {}
        message = data.get("message", str(exc))
        raise GitHubAPIError(f"GitHub API error ({exc.status}): {message}") from exc
    except (GitHubAPIError, GithubTokenError):
        raise
    except Exception as exc:
        raise GitHubAPIError(f"Unexpected error fetching PR #{pr_number}") from exc


@tool
def get_pull_request(repo: str, pr_number: int) -> dict[str, Any]:
    """Fetch a pull request's metadata and bounded changed-file patches."""
    return fetch_pull_request(repo, pr_number)
