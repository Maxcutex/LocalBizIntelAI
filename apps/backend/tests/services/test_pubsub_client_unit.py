from contextlib import contextmanager
from typing import Any

from api.config import Settings
from services.pubsub_client import PubSubClient


@contextmanager
def _disable_dotenv_for_settings() -> Any:
    old_env_file = Settings.model_config.get("env_file")
    Settings.model_config["env_file"] = None
    try:
        yield
    finally:
        Settings.model_config["env_file"] = old_env_file


def test_pubsub_client_noop_when_disabled() -> None:
    with _disable_dotenv_for_settings():
        settings = Settings(pubsub_enabled=False)
        client = PubSubClient(settings=settings)
        client.publish_ingestion_job(topic="ingestion-jobs", message={"hello": "world"})


def test_pubsub_client_noop_when_library_missing() -> None:
    with _disable_dotenv_for_settings():
        settings = Settings(pubsub_enabled=True, gcp_project_id="proj")
        client = PubSubClient(settings=settings)
        client.publish_ingestion_job(topic="ingestion-jobs", message={"hello": "world"})
