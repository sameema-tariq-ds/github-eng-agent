from __future__ import annotations

import logging
from datetime import UTC, datetime

from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from src.agent.nodes.executor import fetch_pr_node, review_node
from src.agent.state import AgentState

logger = logging.getLogger(__name__)

memory = MemorySaver()

builder = StateGraph(AgentState)
builder.add_node("fetch_pull_request", fetch_pr_node)
builder.add_node("review_pull_request", review_node)
builder.add_edge(START, "fetch_pull_request")
builder.add_edge("fetch_pull_request", "review_pull_request")
builder.add_edge("review_pull_request", END)
graph = builder.compile(checkpointer=memory)


def run(
    *,
    repository: str,
    pull_request_number: int,
    delivery_id: str,
    commit_sha: str,
    action: str,
) -> AgentState:
    """Execute one bounded, auditable PR-review job."""
    state: AgentState = {
        "delivery_id": delivery_id,
        "repository": repository,
        "pull_request_number": pull_request_number,
        "commit_sha": commit_sha,
        "action": action,
        "objective": "Review the pull request",
        "messages": [],
        "findings": [],
        "tool_calls": 0,
        "retry_count": 0,
        "status": "running",
        "error": None,
        "started_at": datetime.now(UTC),
        "completed_at": None,
    }
    try:
        return graph.invoke(
            state,
            config={
                "configurable": {
                "thread_id": delivery_id
                }
            }
        )
    except Exception:
        logger.exception("Agent run failed delivery_id=%s", delivery_id)
        raise
