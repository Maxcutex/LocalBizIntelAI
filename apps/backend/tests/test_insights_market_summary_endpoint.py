from uuid import UUID, uuid4

from api.dependencies import CurrentRequestContext, get_current_request_context, get_db
from api.main import create_app
from api.routers import insights as insights_router


def override_db():
    class DummySession:
        pass

    yield DummySession()


def test_generate_market_summary_success():
    app = create_app()
    expected_tenant_id = uuid4()

    class FakeInsightService:
        def generate_market_summary(
            self,
            db_session,
            city: str,
            country: str | None,
            tenant_id: UUID,
            regions: list[str] | None = None,
        ):
            assert city == "Accra"
            assert country == "GH"
            assert tenant_id == expected_tenant_id
            assert regions == ["accra-1"]
            return {
                "city": city,
                "country": country,
                "stats": {},
                "ai_summary": {"summary": "ok"},
            }

    def override_context():
        return CurrentRequestContext(user_id=uuid4(), tenant_id=expected_tenant_id)

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_request_context] = override_context
    app.dependency_overrides[insights_router.get_insight_service] = (
        lambda: FakeInsightService()
    )

    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.post(
        "/insights/market-summary",
        json={"city": "Accra", "country": "GH", "regions": ["accra-1"]},
    )

    assert response.status_code == 200
    assert response.json()["ai_summary"]["summary"] == "ok"


def test_generate_market_summary_missing_headers_returns_401():
    app = create_app()
    app.dependency_overrides[get_db] = override_db

    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.post("/insights/market-summary", json={"city": "Accra"})

    assert response.status_code == 401
