from datetime import datetime

import pytest
from fastapi import HTTPException

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

    service = MarketService(demographics_repository=FakeDemographicsRepository())
    result = service.get_demographics_by_region(None, "Accra", None)

    assert result[0]["geo_id"] == "accra-1"
    assert result[0]["population_total"] == 1000


def test_get_demographics_by_region_raises_404_when_empty():
    class FakeDemographicsRepository:
        def list_by_city(self, db_session, city, country):
            return []

    service = MarketService(demographics_repository=FakeDemographicsRepository())

    with pytest.raises(HTTPException) as exc_info:
        service.get_demographics_by_region(None, "Accra", None)

    assert exc_info.value.status_code == 404
