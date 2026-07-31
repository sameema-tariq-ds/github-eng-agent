# github-eng-agent
AI-powered autonomous engineering agent that monitors GitHub pull requests, analyzes CI/CD failures, performs root cause analysis, and generates automated code fixes using multi-agent LLM orchestration.

## Current PR review flow

1. `src/api/endpoints/webhook.py` verifies the raw GitHub signature.
2. `src/api/validators/` parses and filters supported pull-request events.
3. `src/core/jobs.py` deduplicates deliveries and publishes an `AgentJob` to Pub/Sub.
4. `src/agent/graph.py` fetches a bounded PR snapshot and generates a structured review.

In production, configure `PUBSUB_TOPIC` as a full Pub/Sub topic path and provide
Application Default Credentials with access to Pub/Sub and Firestore. The local
in-process fallback is allowed only outside production. Review posting is disabled
by default until an explicit, audited GitHub write workflow is added.
