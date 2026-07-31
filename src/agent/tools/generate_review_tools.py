from __future__ import annotations

from typing import Any

from langchain_core.tools import tool
from src.llm.client import call_ollama
from src.llm.prompts import build_review_prompt


@tool
def generate_review(pr_info: dict[str, Any], repository: str, pr_number: int) -> dict:
    """Analyze a pull-request diff and return structured review findings."""
    diff = "\n\n".join(
        f"diff -- {item['filename']}\n{item['patch']}"
        for item in pr_info.get("files", [])
    )

    prompt = build_review_prompt(
        diff,
        {
            "repo_full_name": repository,
            "pr_number": pr_number,
            "changed_files": pr_info.get("changed_files", 0),
        },
    )

    review = call_ollama(prompt)
    return review.model_dump()
