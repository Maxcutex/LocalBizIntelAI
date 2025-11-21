from datetime import datetime

import pytest
from fastapi import HTTPException

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

    service = MarketService(business_density_repository=FakeBusinessDensityRepository())
    result = service.get_business_density(None, "Accra", None, None)

    assert result[0]["business_type"] == "retail"
    assert result[0]["count"] == 10


def test_get_business_density_raises_404_when_empty():
    class FakeBusinessDensityRepository:
        def list_by_city_and_type(self, db_session, city, country, business_type):
            return []

    service = MarketService(business_density_repository=FakeBusinessDensityRepository())

    with pytest.raises(HTTPException) as exc_info:
        service.get_business_density(None, "Accra", None, None)

    assert exc_info.value.status_code == 404
