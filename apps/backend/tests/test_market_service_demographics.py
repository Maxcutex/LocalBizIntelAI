from datetime import datetime

import pytest
from fastapi import HTTPException

from services.dependencies import MarketServiceDependencies
from services.market_service import MarketService


class FakeDemographicsRow:
    def __init__(self):
        self.geo_id = "accra-1"
        self.country = "GH"
        self.city = "Accra"
        self.population_total = 1000
        self.median_income = 200
        self.age_distribution = {"0-18": 0.4}
        self.education_levels = None
        self.household_size_avg = None
        self.immigration_ratio = None
        self.coordinates = None
        self.last_updated = datetime.utcnow()


def test_get_demographics_by_region_maps_rows():
    class FakeDemographicsRepository:
        def list_by_city(self, db_session, city, country):
            return [FakeDemographicsRow()]

    class DummyBusinessDensityRepository:
        def distinct_cities(self, db_session, country):
            raise AssertionError("not used")

        def list_by_city_and_type(self, db_session, city, country, business_type):
            raise AssertionError("not used")

        def get_summary(self, db_session, city, country):
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
            demographics_repository=FakeDemographicsRepository(),
            business_density_repository=DummyBusinessDensityRepository(),
            spending_repository=DummySpendingRepository(),
            labour_stats_repository=DummyLabourStatsRepository(),
        )
    )
    result = service.get_demographics_by_region(None, "Accra", None)

    assert result[0]["geo_id"] == "accra-1"
    assert result[0]["population_total"] == 1000


def test_get_demographics_by_region_raises_404_when_empty():
    class FakeDemographicsRepository:
        def list_by_city(self, db_session, city, country):
            return []

    class DummyBusinessDensityRepository:
        def distinct_cities(self, db_session, country):
            raise AssertionError("not used")

        def list_by_city_and_type(self, db_session, city, country, business_type):
            raise AssertionError("not used")

        def get_summary(self, db_session, city, country):
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
            demographics_repository=FakeDemographicsRepository(),
            business_density_repository=DummyBusinessDensityRepository(),
            spending_repository=DummySpendingRepository(),
            labour_stats_repository=DummyLabourStatsRepository(),
        )
    )

    with pytest.raises(HTTPException) as exc_info:
        service.get_demographics_by_region(None, "Accra", None)

    assert exc_info.value.status_code == 404
