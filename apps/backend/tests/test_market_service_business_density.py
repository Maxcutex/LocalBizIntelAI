from datetime import datetime

import pytest
from fastapi import HTTPException

from services.dependencies import MarketServiceDependencies
from services.market_service import MarketService


class FakeBusinessDensityRow:
    def __init__(self):
        self.geo_id = "accra-1"
        self.country = "GH"
        self.city = "Accra"
        self.business_type = "retail"
        self.count = 10
        self.density_score = 0.6
        self.coordinates = None
        self.last_updated = datetime.utcnow()


def test_get_business_density_maps_rows():
    class FakeBusinessDensityRepository:
        def list_by_city_and_type(self, db_session, city, country, business_type):
            return [FakeBusinessDensityRow()]

    class DummyDemographicsRepository:
        def distinct_cities(self, db_session, country):
            raise AssertionError("not used")

        def list_by_city(self, db_session, city, country):
            raise AssertionError("not used")

        def get_city_aggregates(self, db_session, city, country):
            raise AssertionError("not used")

    class DummySpendingRepository:
        def get_for_regions(self, db_session, city, country):
            raise AssertionError("not used")

        def get_city_aggregates(self, db_session, city, country):
            raise AssertionError("not used")

    class DummyLabourStatsRepository:
        def get_for_regions(self, db_session, city, country):
            raise AssertionError("not used")

        def get_city_aggregates(self, db_session, city, country):
            raise AssertionError("not used")

    service = MarketService(
        MarketServiceDependencies(
            demographics_repository=DummyDemographicsRepository(),
            business_density_repository=FakeBusinessDensityRepository(),
            spending_repository=DummySpendingRepository(),
            labour_stats_repository=DummyLabourStatsRepository(),
        )
    )
    result = service.get_business_density(None, "Accra", None, None)

    assert result[0]["business_type"] == "retail"
    assert result[0]["count"] == 10


def test_get_business_density_raises_404_when_empty():
    class FakeBusinessDensityRepository:
        def list_by_city_and_type(self, db_session, city, country, business_type):
            return []

    class DummyDemographicsRepository:
        def distinct_cities(self, db_session, country):
            raise AssertionError("not used")

        def list_by_city(self, db_session, city, country):
            raise AssertionError("not used")

        def get_city_aggregates(self, db_session, city, country):
            raise AssertionError("not used")

    class DummySpendingRepository:
        def get_for_regions(self, db_session, city, country):
            raise AssertionError("not used")

        def get_city_aggregates(self, db_session, city, country):
            raise AssertionError("not used")

    class DummyLabourStatsRepository:
        def get_for_regions(self, db_session, city, country):
            raise AssertionError("not used")

        def get_city_aggregates(self, db_session, city, country):
            raise AssertionError("not used")

    service = MarketService(
        MarketServiceDependencies(
            demographics_repository=DummyDemographicsRepository(),
            business_density_repository=FakeBusinessDensityRepository(),
            spending_repository=DummySpendingRepository(),
            labour_stats_repository=DummyLabourStatsRepository(),
        )
    )

    with pytest.raises(HTTPException) as exc_info:
        service.get_business_density(None, "Accra", None, None)

    assert exc_info.value.status_code == 404
