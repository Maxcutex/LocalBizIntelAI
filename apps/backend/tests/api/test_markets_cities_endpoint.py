"""HTTP endpoint tests for listing market cities."""

from api.dependencies import get_db
from api.main import create_app
from api.routers import markets as markets_router


def override_db():
    """Provide a dummy DB session for dependency overrides."""

    class DummySession:
        """Stub SQLAlchemy session."""

    yield DummySession()


def test_list_cities_success():
    """`GET /markets/cities` returns all cities when no country filter."""
    app = create_app()

    class FakeMarketService:
        """Fake market service returning canned cities."""

        def list_cities(self, _db_session, country):
            """Return cities for a country filter."""
            assert country is None
            return ["Accra", "Lagos"]

    app.dependency_overrides[get_db] = override_db

    def override_market_service():
        """Provide fake market service."""
        return FakeMarketService()

    app.dependency_overrides[markets_router.get_market_service] = (
        override_market_service
    )

    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.get("/markets/cities")

    assert response.status_code == 200
    assert response.json() == {"cities": ["Accra", "Lagos"]}


def test_list_cities_with_country_param():
    """Country param is forwarded to service."""
    app = create_app()

    class FakeMarketService:
        """Fake market service returning cities for given country."""

        def list_cities(self, _db_session, country):
            """Return cities."""
            assert country == "NG"
            return ["Lagos"]

    app.dependency_overrides[get_db] = override_db

    def override_market_service():
        """Provide fake market service."""
        return FakeMarketService()

    app.dependency_overrides[markets_router.get_market_service] = (
        override_market_service
    )

    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.get("/markets/cities?country=NG")

    assert response.status_code == 200
    assert response.json() == {"cities": ["Lagos"]}


def test_list_cities_empty_result():
    """Empty service results yield empty list."""
    app = create_app()

    class FakeMarketService:
        """Fake market service returning no cities."""

        def list_cities(self, _db_session, _country):
            """Return empty list."""
            return []

    app.dependency_overrides[get_db] = override_db

    def override_market_service():
        """Provide fake market service."""
        return FakeMarketService()

    app.dependency_overrides[markets_router.get_market_service] = (
        override_market_service
    )

    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.get("/markets/cities")

    assert response.status_code == 200
    assert response.json() == {"cities": []}
