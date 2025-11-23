from uuid import uuid4

from services.dependencies import MarketServiceDependencies
from services.market_service import MarketService


def test_market_service_get_overview_combines_repository_outputs():
    class FakeDemographicsRepository:
        def get_city_aggregates(self, db_session, city, country):
            return {"population_total": 1000}

    class FakeSpendingRepository:
        def get_city_aggregates(self, db_session, city, country):
            return {"avg_monthly_spend": 120.0}

    class FakeLabourStatsRepository:
        def get_city_aggregates(self, db_session, city, country):
            return {"avg_unemployment_rate": 0.05}

    class FakeBusinessDensityRepository:
        def get_summary(self, db_session, city, country):
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
