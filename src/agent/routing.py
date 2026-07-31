from __future__ import annotations

from src.agent.state import AgentState


def route_after_pr_fetch(state: AgentState) -> str:
    """Determine the next graph node after fetching the pull request.

    Routes to the error handler if an error exists in the state;
    otherwise, proceeds to the next processing step.
    """
    return "failed" if state.get("error") else "completed"
