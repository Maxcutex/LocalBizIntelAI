"""Pytest configuration and shared fixtures."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from api.main import create_app


@pytest.fixture(scope="session")
def app():
    """Create a fresh FastAPI app instance for tests."""

    return create_app()


@pytest.fixture(scope="session")
def client(app) -> Generator[TestClient, None, None]:
    """Sync test client for calling the API."""

    with TestClient(app) as c:
        yield c
