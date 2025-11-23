from uuid import uuid4

from api.dependencies import CurrentRequestContext, get_current_request_context, get_db
from api.main import create_app
from api.routers import insights as insights_router
from services.dependencies import InsightServiceDependencies
from services.insight_service import InsightService


def override_db():
    class DummySession:
        pass

    yield DummySession()


def test_opportunities_http_smoke_real_service_orders_and_includes_ai():
    app = create_app()
    expected_tenant_id = uuid4()

    class FakeOpportunityRow:
        def __init__(self, geo_id: str, composite_score: float):
            self.geo_id = geo_id
            self.country = "CA"
            self.city = "Toronto"
            self.business_type = "restaurant"
            self.demand_score = 0.8
            self.supply_score = 0.4
            self.competition_score = 0.2
            self.composite_score = composite_score
            self.calculated_at = None

    class FakeOpportunityRepository:
        def list_by_city_and_business_type(
            self, db_session, city, country, business_type
        ):
            return [
                FakeOpportunityRow("toronto-a", 0.3),
                FakeOpportunityRow("toronto-b", 0.9),
            ]

    class FakeAiClient:
        def generate_opportunity_commentary(self, ranked_regions):
            return {"commentary": "ai", "region_rationales": []}

    def override_context():
        return CurrentRequestContext(user_id=uuid4(), tenant_id=expected_tenant_id)

    def override_insight_service():
        class DummyDemographicsRepository:
            def get_for_regions(self, db_session, city, country):
                return []

        class DummySpendingRepository:
            def get_for_regions(self, db_session, city, country):
                return []

        class DummyLabourStatsRepository:
            def get_for_regions(self, db_session, city, country):
                return []

        return InsightService(
            InsightServiceDependencies(
                demographics_repository=DummyDemographicsRepository(),
                spending_repository=DummySpendingRepository(),
                labour_stats_repository=DummyLabourStatsRepository(),
                opportunity_scores_repository=FakeOpportunityRepository(),
                ai_engine_client=FakeAiClient(),
            )
        )

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_request_context] = override_context
    app.dependency_overrides[insights_router.get_insight_service] = (
        override_insight_service
    )

    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.post(
        "/insights/opportunities",
        json={"city": "Toronto", "country": "CA", "business_type": "restaurant"},
    )

    assert response.status_code == 200
    body = response.json()
    assert [r["geo_id"] for r in body["opportunities"]] == [
        "toronto-b",
        "toronto-a",
    ]
    assert body["ai_commentary"]["commentary"] == "ai"
