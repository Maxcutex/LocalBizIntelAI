"""HTTP endpoint tests for market demographics routes."""

from api.dependencies import get_db
from api.main import create_app
from api.routers import markets as markets_router


def override_db():
    """Provide a dummy DB session for dependency overrides."""

    class DummySession:
        """Stub SQLAlchemy session."""

    yield DummySession()


def test_get_market_demographics_success():
    """`GET /markets/{city}/demographics` returns demographics for city."""
    app = create_app()

    class FakeMarketService:
        """Fake market service returning canned demographics."""

        def get_demographics_by_region(self, _db_session, city, country):
            """Return deterministic demographics list."""
            assert city == "Accra"
            assert country == "GH"
            return [
                {
                    "geo_id": "accra-1",
                    "country": "GH",
                    "city": "Accra",
                    "population_total": 1000,
                    "median_income": 200.0,
                    "age_distribution": None,
                    "education_levels": None,
                    "household_size_avg": None,
                    "immigration_ratio": None,
                    "coordinates": None,
                    "last_updated": None,
                }
            ]

    app.dependency_overrides[get_db] = override_db

    def override_market_service():
        """Provide the fake market service."""
        return FakeMarketService()

    app.dependency_overrides[markets_router.get_market_service] = (
        override_market_service
    )

    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.get("/markets/Accra/demographics?country=GH")

    assert response.status_code == 200
    data = response.json()
    assert data["city"] == "Accra"
    assert data["country"] == "GH"
    assert len(data["demographics"]) == 1


def test_get_market_demographics_not_found():
    """Missing demographics yields 404."""
    app = create_app()

    class FakeMarketService:
        """Fake market service raising 404."""

        def get_demographics_by_region(self, _db_session, _city, _country):
            """Raise 404 for any lookup."""
            from fastapi import HTTPException, status

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Demographics not found for city",
            )

    app.dependency_overrides[get_db] = override_db

    def override_market_service():
        """Provide the fake market service."""
        return FakeMarketService()

    app.dependency_overrides[markets_router.get_market_service] = (
        override_market_service
    )

    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.get("/markets/Nowhere/demographics")

    assert response.status_code == 404
