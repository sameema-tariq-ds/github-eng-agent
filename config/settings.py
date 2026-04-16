import os
from dotenv import load_dotenv
load_dotenv()

ENV = os.getenv("ENV", "development")

class Settings:
    """
    Central configuration loader for eng-agent.
    Works with:
    - Cloud Run (env vars injected from Secret Manager)
    - Local dev (.env optional)
    """

    def __init__(self) -> None:
        self.GCP_PROJECT_ID = self._get_required("GCP_PROJECT_ID")

        self.GITHUB_WEBHOOK_SECRET = self._get_required("GITHUB_WEBHOOK_SECRET")

        self.GITHUB_APP_PRIVATE_KEY_PEM = self._get_required("GITHUB_APP_PRIVATE_KEY_PEM")

        self.OPENROUTER_API_KEY = self._get_required("OPENROUTER_API_KEY")

        self.ALLOWED_EVENTS = {"pull_request", "workflow_run", "check_run"}

    # -----------------------------
    # Core safety helper
    # -----------------------------
    def _get_required(self, key: str) -> str:
        """
        Fetch required environment variable.
        Raises RuntimeError if missing (fail-fast principle).
        """
        value = os.getenv(key)

        if not value:
            if ENV == "development":
                print(f"[WARNING] Missing {key}, using dummy value")
                return "dummy"
            raise RuntimeError(f"Missing required environment variable: {key}")

        return value


# Singleton instance (used across app)
settings = Settings()