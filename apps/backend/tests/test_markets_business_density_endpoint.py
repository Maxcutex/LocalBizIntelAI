from api.dependencies import get_db
from api.main import create_app
from api.routers import markets as markets_router


def override_db():
    class DummySession:
        pass

    yield DummySession()


def test_get_business_density_success_with_filter():
    app = create_app()

    class FakeMarketService:
        def get_business_density(self, db_session, city, country, business_type):
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
    app.dependency_overrides[markets_router.get_market_service] = (
        lambda: FakeMarketService()
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
    app = create_app()

    class FakeMarketService:
        def get_business_density(self, db_session, city, country, business_type):
            from fastapi import HTTPException, status

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business density not found for city",
            )

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[markets_router.get_market_service] = (
        lambda: FakeMarketService()
    )

    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.get("/markets/Nowhere/business-density")

    assert response.status_code == 404
