"""Typed models for LLM review requests and responses."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ReviewIssue(BaseModel):
    """One actionable finding returned by the reviewer."""

    model_config = ConfigDict(extra="forbid")

    file: str = Field(min_length=1)
    line: int | None = Field(default=None, ge=1)
    # LEFT → the old version of the file (before the PR
    # RIGHT → the new version of the file (the changes introduced by the PR)
    side: Literal["RIGHT", "LEFT"] = "RIGHT" 
    severity: Literal["blocker", "warning", "info"]
    comment: str = Field(min_length=1)


class ReviewOutput(BaseModel):
    """Validated structured output produced by the LLM reviewer."""

    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=1)
    issues: list[ReviewIssue] = Field(default_factory=list)