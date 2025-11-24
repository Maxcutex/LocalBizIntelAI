"""Unit tests for `MarketService.get_demographics_by_region`."""

from datetime import datetime

import pytest
from fastapi import HTTPException

from services.dependencies import MarketServiceDependencies
from services.market_service import MarketService


class FakeDemographicsRow:
    """Row-like fixture representing a demographics ORM row."""

    def __init__(self):
        """Populate fixture fields."""
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
    """Service maps ORM rows into response dicts."""

    class FakeDemographicsRepository:
        """Fake demographics repository returning canned rows."""

        def list_by_city(self, db_session, city, country):
            """Return one demographics row."""
            _ = db_session
            _ = city
            _ = country
            return [FakeDemographicsRow()]

    class DummyBusinessDensityRepository:
        """Stub business density repository (unused)."""

        def distinct_cities(self, _db_session, _country):
            """Not used in this test."""
            raise AssertionError("not used")

        def list_by_city_and_type(self, _db_session, _city, _country, _business_type):
            """Not used in this test."""
            raise AssertionError("not used")

        def get_summary(self, _db_session, _city, _country):
            """Not used in this test."""
            raise AssertionError("not used")

    class DummySpendingRepository:
        """Stub spending repository (unused)."""

        def get_for_regions(self, _db_session, _city, _country):
            """Not used in this test."""
            raise AssertionError("not used")

        def get_city_aggregates(self, _db_session, _city, _country):
            """Not used in this test."""
            raise AssertionError("not used")

    class DummyLabourStatsRepository:
        """Stub labour stats repository (unused)."""

        def get_for_regions(self, _db_session, _city, _country):
            """Not used in this test."""
            raise AssertionError("not used")

        def get_city_aggregates(self, _db_session, _city, _country):
            """Not used in this test."""
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
    """Empty repository results raise 404."""

    class FakeDemographicsRepository:
        """Fake demographics repository returning no rows."""

        def list_by_city(self, db_session, city, country):
            """Return empty list."""
            _ = db_session
            _ = city
            _ = country
            return []

    class DummyBusinessDensityRepository:
        """Stub business density repository (unused)."""

        def distinct_cities(self, _db_session, _country):
            """Not used in this test."""
            raise AssertionError("not used")

        def list_by_city_and_type(self, _db_session, _city, _country, _business_type):
            """Not used in this test."""
            raise AssertionError("not used")

        def get_summary(self, _db_session, _city, _country):
            """Not used in this test."""
            raise AssertionError("not used")

    class DummySpendingRepository:
        """Stub spending repository (unused)."""

        def get_for_regions(self, _db_session, _city, _country):
            """Not used in this test."""
            raise AssertionError("not used")

        def get_city_aggregates(self, _db_session, _city, _country):
            """Not used in this test."""
            raise AssertionError("not used")

    class DummyLabourStatsRepository:
        """Stub labour stats repository (unused)."""

        def get_for_regions(self, _db_session, _city, _country):
            """Not used in this test."""
            raise AssertionError("not used")

        def get_city_aggregates(self, _db_session, _city, _country):
            """Not used in this test."""
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
