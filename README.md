# github-eng-agent
AI-powered autonomous engineering agent that monitors GitHub pull requests, analyzes CI/CD failures, performs root cause analysis, and generates automated code fixes using multi-agent LLM orchestration.

## PR review flow

The structure for automated PR reviews is:

1. `api/v1/endpoints/webhook.py` validates the GitHub signature and queues supported PR events.
2. `agent/orchestrator.py` converts the payload into a `PullRequestRef` and runs the reviewer.
3. `agent/tools/github_client.py` fetches changed files and commit checks.
4. `agent/tools/llm_client.py` asks the configured model for structured findings.
5. `agent/agents/pr_reviewer.py` returns `ready_to_merge`, a summary, and findings.

Set `GITHUB_POST_REVIEW=true` to post the result as a GitHub issue comment. For production, replace FastAPI `BackgroundTasks` with the existing Pub/Sub path so retries and deduplication are durable.
