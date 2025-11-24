"""Unit tests for `MarketService.get_overview` aggregation."""

from uuid import uuid4

from services.dependencies import MarketServiceDependencies
from services.market_service import MarketService


def test_market_service_get_overview_combines_repository_outputs():
    """Overview combines aggregates from all repositories."""

    class FakeDemographicsRepository:
        """Fake demographics repository."""

        def get_city_aggregates(self, _db_session, _city, _country):
            """Return canned demographics aggregates."""
            return {"population_total": 1000}

    class FakeSpendingRepository:
        """Fake spending repository."""

        def get_city_aggregates(self, _db_session, _city, _country):
            """Return canned spending aggregates."""
            return {"avg_monthly_spend": 120.0}

    class FakeLabourStatsRepository:
        """Fake labour stats repository."""

        def get_city_aggregates(self, _db_session, _city, _country):
            """Return canned labour aggregates."""
            return {"avg_unemployment_rate": 0.05}

    class FakeBusinessDensityRepository:
        """Fake business density repository."""

        def get_summary(self, _db_session, _city, _country):
            """Return canned density summary."""
            return {"total_business_count": 200}

    service = MarketService(
        MarketServiceDependencies(
            demographics_repository=FakeDemographicsRepository(),
            business_density_repository=FakeBusinessDensityRepository(),
            spending_repository=FakeSpendingRepository(),
            labour_stats_repository=FakeLabourStatsRepository(),
        )
    )

    overview = service.get_overview(
        db_session=None,
        city="Accra",
        country=None,
        tenant_id=uuid4(),
    )

    assert overview["city"] == "Accra"
    assert overview["country"] is None
    assert overview["demographics"] == {"population_total": 1000}
    assert overview["spending"] == {"avg_monthly_spend": 120.0}
    assert overview["labour_stats"] == {"avg_unemployment_rate": 0.05}
    assert overview["business_density"] == {"total_business_count": 200}
