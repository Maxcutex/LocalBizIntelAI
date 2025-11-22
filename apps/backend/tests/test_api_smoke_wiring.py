from uuid import uuid4

from api.dependencies import CurrentRequestContext, get_current_request_context, get_db
from api.main import create_app
from api.routers import markets as markets_router


def override_db():
    class DummySession:
        pass

    yield DummySession()


def test_health_and_markets_cities_smoke():
    app = create_app()

    class FakeMarketService:
        def list_cities(self, db_session, country):
            assert country == "CA"
            return ["Toronto"]

    def override_context():
        return CurrentRequestContext(user_id=uuid4(), tenant_id=uuid4(), role="USER")

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_request_context] = override_context
    app.dependency_overrides[markets_router.get_market_service] = (
        lambda: FakeMarketService()
    )

    from fastapi.testclient import TestClient

    client = TestClient(app)
    health = client.get("/health")
    assert health.status_code == 200

    cities = client.get("/markets/cities?country=CA")
    assert cities.status_code == 200
    assert cities.json()["cities"] == ["Toronto"]
