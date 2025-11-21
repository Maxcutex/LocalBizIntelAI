from api.dependencies import get_db
from api.main import create_app
from api.routers import markets as markets_router


def override_db():
    class DummySession:
        pass

    yield DummySession()


def test_get_market_demographics_success():
    app = create_app()

    class FakeMarketService:
        def get_demographics_by_region(self, db_session, city, country):
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
    app.dependency_overrides[markets_router.get_market_service] = (
        lambda: FakeMarketService()
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
    app = create_app()

    class FakeMarketService:
        def get_demographics_by_region(self, db_session, city, country):
            from fastapi import HTTPException, status

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Demographics not found for city",
            )

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[markets_router.get_market_service] = (
        lambda: FakeMarketService()
    )

    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.get("/markets/Nowhere/demographics")

    assert response.status_code == 404
