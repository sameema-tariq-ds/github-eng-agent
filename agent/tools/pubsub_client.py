# agent\tools\pubsub_client.py
import os
from google.cloud import pubsub_v1

class PubSubClient:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.env = os.getenv("ENV", "development")
        self._client = None

    def publish(self, topic_name: str, message: bytes):
        if self.env == "development":
            print(f"[MOCK PUBSUB] topic={topic_name} message={message}")
            return

        if self._client is None:
            self._client = pubsub_v1.PublisherClient()

        topic_path = self._client.topic_path(self.project_id, topic_name)
        self._client.publish(topic_path, message)

        