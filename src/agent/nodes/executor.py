from __future__ import annotations

from datetime import UTC, datetime

from src.agent.state import AgentState
from src.agent.tools.pull_request_tools import get_pull_request
from src.core.config import get_settings
from src.agent.tools.generate_review_tools import generate_review


def fetch_pr_node(state: AgentState) -> AgentState:
    """Load the PR snapshot used by all later agent steps."""
    try:
        pr_info = get_pull_request.invoke(
            {
                "repo": state["repository"],
                "pr_number": state["pull_request_number"],
            }
        )
        return {
            **state, 
            "pr_info": pr_info, 
            "tool_calls": state.get("tool_calls", 0) + 1
        }
    except Exception as exc:
        return {
            **state,
            "status": "failed",
            "error": str(exc),
            "completed_at": datetime.now(UTC),
        }


def review_node(state: AgentState) -> AgentState:
    """Generate a validated review from the bounded PR snapshot."""
    if state.get("error"):
        return state
    if state.get("tool_calls", 0) > get_settings().max_agent_tool_calls:
        return {**state, "status": "failed", "error": "Agent tool-call limit exceeded"}
    pr_info = state.get("pr_info", {})
    
    try:
        review = generate_review.invoke(
            {
                "pr_info": pr_info,
                "repository": state["repository"],
                "pr_number": state["pull_request_number"],
            }
        )
        return {
            **state,
            "review": review,
            "status": "completed",
            "completed_at": datetime.now(UTC),
            "tool_calls": state.get("tool_calls", 0) + 1,
        }
    except Exception:
        return {
            **state,
            "status": "failed",
            "error": "Review generation failed",
            "completed_at": datetime.now(UTC),
        }
