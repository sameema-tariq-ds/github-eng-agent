# github-eng-agent
AI-powered autonomous engineering agent that monitors GitHub pull requests, analyzes CI/CD failures, performs root cause analysis, and generates automated code fixes using multi-agent LLM orchestration.

## PR review flow

The structure for automated PR reviews is:

1. `api/v1/endpoints/webhook.py` validates the GitHub signature and queues supported PR events.
2. `src/agent/agents/router.py` routes supported events to the reviewer workflow.
3. `src/agent/tools/github_client.py` fetches the diff and posts the review.
4. `src/agent/tools/review_generator.py` asks the configured model for structured findings.
5. `src/agent/agents/pr_reviewer.py` coordinates the tools and publishes the result.

Set `GITHUB_POST_REVIEW=true` to post the result as a GitHub issue comment. For production, replace FastAPI `BackgroundTasks` with the existing Pub/Sub path so retries and deduplication are durable.
