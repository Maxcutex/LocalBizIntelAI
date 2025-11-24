"""Smoke tests to ensure router wiring and basic endpoints respond."""

from uuid import uuid4

from api.dependencies import CurrentRequestContext, get_current_request_context, get_db
from api.main import create_app
from api.routers import markets as markets_router


def override_db():
    """Provide a dummy DB session for dependency overrides."""

    class DummySession:
        """Stub SQLAlchemy session."""

    yield DummySession()


def test_health_and_markets_cities_smoke():
    """`GET /health` and `GET /markets/cities` succeed with overrides."""
    app = create_app()

    class FakeMarketService:
        """Fake market service returning canned cities."""

        def list_cities(self, _db_session, country):
            """Return list of cities for given country."""
            assert country == "CA"
            return ["Toronto"]

    def override_context():
        """Provide a fake request context."""
        return CurrentRequestContext(user_id=uuid4(), tenant_id=uuid4(), role="USER")

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_request_context] = override_context

    def override_market_service():
        """Provide the fake market service."""
        return FakeMarketService()

    app.dependency_overrides[markets_router.get_market_service] = (
        override_market_service
    )

    from fastapi.testclient import TestClient

    client = TestClient(app)
    health = client.get("/health")
    assert health.status_code == 200

    cities = client.get("/markets/cities?country=CA")
    assert cities.status_code == 200
    assert cities.json()["cities"] == ["Toronto"]
