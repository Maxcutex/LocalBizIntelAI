"""HTTP endpoint tests for market business density routes."""

from api.dependencies import get_db
from api.main import create_app
from api.routers import markets as markets_router


def override_db():
    """Provide a dummy DB session for dependency overrides."""

    class DummySession:
        """Stub SQLAlchemy session."""

    yield DummySession()


def test_get_business_density_success_with_filter():
    """`GET /markets/{city}/business-density` returns density for filter."""
    app = create_app()

    class FakeMarketService:
        """Fake market service returning canned densities."""

        def get_business_density(self, _db_session, city, country, business_type):
            """Return deterministic density list."""
            assert city == "Accra"
            assert country == "GH"
            assert business_type == "retail"
            return [
                {
                    "geo_id": "accra-1",
                    "country": "GH",
                    "city": "Accra",
                    "business_type": "retail",
                    "count": 10,
                    "density_score": 0.6,
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
    response = client.get(
        "/markets/Accra/business-density?country=GH&business_type=retail"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["city"] == "Accra"
    assert data["business_type"] == "retail"
    assert len(data["business_density"]) == 1


def test_get_business_density_not_found():
    """Missing density yields 404."""
    app = create_app()

    class FakeMarketService:
        """Fake market service raising 404."""

        def get_business_density(self, _db_session, _city, _country, _business_type):
            """Raise 404 for any lookup."""
            from fastapi import HTTPException, status

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business density not found for city",
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
    response = client.get("/markets/Nowhere/business-density")

    assert response.status_code == 404
