"""Provider-specific LLM adapter."""

from __future__ import annotations

import json
from typing import Any

import httpx


class LLMClient:
    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def review(self, *, title: str, description: str, diff: str, checks: str) -> dict[str, Any]:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        schema = ('{"summary":"string", "findings":[{"severity":"blocker|warning|info", '
                  '"title":"string", "explanation":"string", "file":"string|null", '
                  '"line":"integer|null"}]}')
        prompt = f"""Review this pull request as a senior engineer.
Return JSON only matching this schema: {schema}.
Only blocker findings prevent merging. Do not treat style preferences as blockers.
Title: {title}
Description: {description}
CI checks: {checks}
Diff:\n{diff}"""
        response = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model, "temperature": 0,
                "response_format": {"type": "json_object"},
                "messages": [{"role": "system", "content": "You are a precise code reviewer."},
                             {"role": "user", "content": prompt}],
            },
            timeout=90,
        )
        response.raise_for_status()
        return json.loads(response.json()["choices"][0]["message"]["content"])
