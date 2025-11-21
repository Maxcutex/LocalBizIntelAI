from uuid import UUID, uuid4

from api.dependencies import CurrentRequestContext, get_current_request_context, get_db
from api.main import create_app
from api.routers import insights as insights_router


def override_db():
    class DummySession:
        pass

    yield DummySession()


def test_generate_opportunities_success():
    app = create_app()
    expected_tenant_id = uuid4()

    class FakeInsightService:
        def find_opportunities(
            self,
            db_session,
            city: str,
            business_type: str | None,
            constraints: dict | None,
            country: str | None,
            tenant_id: UUID,
        ):
            assert city == "Accra"
            assert business_type == "retail"
            assert constraints == {"min_composite_score": 0.5}
            assert country == "GH"
            assert tenant_id == expected_tenant_id
            return {
                "city": city,
                "country": country,
                "business_type": business_type,
                "opportunities": [{"geo_id": "accra-1", "composite_score": 0.9}],
                "ai_commentary": {"commentary": "ok"},
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
        "/insights/opportunities",
        json={
            "city": "Accra",
            "country": "GH",
            "business_type": "retail",
            "constraints": {"min_composite_score": 0.5},
        },
    )

    assert response.status_code == 200
    assert response.json()["ai_commentary"]["commentary"] == "ok"


def test_generate_opportunities_missing_headers_returns_401():
    app = create_app()
    app.dependency_overrides[get_db] = override_db

    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.post("/insights/opportunities", json={"city": "Accra"})

    assert response.status_code == 401
