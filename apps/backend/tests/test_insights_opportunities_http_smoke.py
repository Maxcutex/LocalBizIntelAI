"""HTTP smoke tests for `/insights/opportunities` endpoint wiring."""

from uuid import uuid4

from api.dependencies import CurrentRequestContext, get_current_request_context, get_db
from api.main import create_app
from api.routers import insights as insights_router
from services.dependencies import InsightServiceDependencies
from services.insight_service import InsightService


def override_db():
    """Provide a dummy DB session for dependency overrides."""

    class DummySession:
        """Stub SQLAlchemy session."""

    yield DummySession()


def test_opportunities_http_smoke_real_service_orders_and_includes_ai():
    """Endpoint returns ranked opportunities and AI commentary."""
    app = create_app()
    expected_tenant_id = uuid4()

    class FakeOpportunityRow:
        """Row-like fixture for opportunity scores."""

        def __init__(self, geo_id: str, composite_score: float):
            """Populate fixture fields."""
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
        """Fake opportunity repository returning two rows."""

        def list_by_city_and_business_type(
            self, _db_session, _city, _country, _business_type
        ):
            """Return canned rows."""
            return [
                FakeOpportunityRow("toronto-a", 0.3),
                FakeOpportunityRow("toronto-b", 0.9),
            ]

    class FakeAiClient:
        """Fake AI client returning canned commentary."""

        def generate_opportunity_commentary(self, ranked_regions):
            """Return commentary payload."""
            _ = ranked_regions
            return {"commentary": "ai", "region_rationales": []}

    def override_context():
        """Provide fake request context with tenant id."""
        return CurrentRequestContext(user_id=uuid4(), tenant_id=expected_tenant_id)

    def override_insight_service():
        """Provide a real `InsightService` wired with fakes."""

        class DummyDemographicsRepository:
            """Stub demographics repository (unused)."""

            def get_for_regions(self, _db_session, _city, _country):
                """Return empty list."""
                return []

        class DummySpendingRepository:
            """Stub spending repository (unused)."""

            def get_for_regions(self, _db_session, _city, _country):
                """Return empty list."""
                return []

        class DummyLabourStatsRepository:
            """Stub labour stats repository (unused)."""

            def get_for_regions(self, _db_session, _city, _country):
                """Return empty list."""
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
