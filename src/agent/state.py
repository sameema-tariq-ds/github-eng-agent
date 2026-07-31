from __future__ import annotations

from typing import Literal
from typing_extensions import NotRequired, TypedDict
from datetime import datetime


class AgentState(TypedDict):
    """Information carried through the agent workflow for one PR event."""

    delivery_id: str  # Unique GitHub webhook ID; prevents duplicate processing.
    repository: str  # Repository name, for example ``owner/project``.
    pull_request_number: int  # Number of the pull request being reviewed.
    commit_sha: str  # Exact PR commit that triggered this review.
    action: str  # GitHub action, such as ``opened`` or ``synchronize``.
    objective: str  # What the agent is expected to accomplish.
    messages: NotRequired[list]  # Conversation messages exchanged with the LLM.
    findings: NotRequired[list]  # Problems or recommendations found by the agent.
    tool_calls: NotRequired[int]  # Number of tools used during this run.
    retry_count: NotRequired[int]  # Number of times this job has been retried.
    status: NotRequired[Literal[
        "running",
        "waiting_for_approval",
        "completed",
        "failed"
    ]]  # Current workflow status.
    error: NotRequired[str | None]  # Error message if the run failed.
    started_at: NotRequired[datetime]  # When the agent started this run.
    completed_at: NotRequired[datetime | None]  # When the agent finished.
    pr_info: NotRequired[dict]  # GitHub data fetched for the pull request.
    review: NotRequired[dict]  # Final structured review produced by the LLM.
