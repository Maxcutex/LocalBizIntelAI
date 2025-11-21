from api.dependencies import get_db
from api.main import create_app
from api.routers import markets as markets_router


def override_db():
    class DummySession:
        pass

    yield DummySession()


def test_list_cities_success():
    app = create_app()

    class FakeMarketService:
        def list_cities(self, db_session, country):
            assert country is None
            return ["Accra", "Lagos"]

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[markets_router.get_market_service] = (
        lambda: FakeMarketService()
    )

    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.get("/markets/cities")

    assert response.status_code == 200
    assert response.json() == {"cities": ["Accra", "Lagos"]}


def test_list_cities_with_country_param():
    app = create_app()

    class FakeMarketService:
        def list_cities(self, db_session, country):
            assert country == "NG"
            return ["Lagos"]

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[markets_router.get_market_service] = (
        lambda: FakeMarketService()
    )

    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.get("/markets/cities?country=NG")

    assert response.status_code == 200
    assert response.json() == {"cities": ["Lagos"]}


def test_list_cities_empty_result():
    app = create_app()

    class FakeMarketService:
        def list_cities(self, db_session, country):
            return []

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[markets_router.get_market_service] = (
        lambda: FakeMarketService()
    )

    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.get("/markets/cities")

    assert response.status_code == 200
    assert response.json() == {"cities": []}
