from uuid import uuid4

import pytest
from fastapi import HTTPException

from services.insight_service import InsightService


def test_generate_market_summary_merges_stats_and_ai():
    class FakeDemographicsRepository:
        def get_for_regions(self, db_session, city, country):
            class FakeRow:
                geo_id = "accra-1"
                population_total = 1000
                median_income = 200

            return [FakeRow()]

    class FakeSpendingRepository:
        def get_for_regions(self, db_session, city, country):
            return []

    class FakeLabourStatsRepository:
        def get_for_regions(self, db_session, city, country):
            return []

    class FakeAiClient:
        def generate_market_summary(self, payload):
            assert payload["city"] == "Accra"
            return {"summary": "ai"}

    service = InsightService(
        demographics_repository=FakeDemographicsRepository(),
        spending_repository=FakeSpendingRepository(),
        labour_stats_repository=FakeLabourStatsRepository(),
        ai_engine_client=FakeAiClient(),
    )

    result = service.generate_market_summary(
        db_session=None,
        city="Accra",
        country=None,
        tenant_id=uuid4(),
        regions=None,
    )

    assert result["city"] == "Accra"
    assert result["ai_summary"] == {"summary": "ai"}
    assert "stats_used" in result


def test_generate_market_summary_raises_404_when_no_data():
    class EmptyDemographicsRepository:
        def get_for_regions(self, db_session, city, country):
            return []

    class EmptySpendingRepository:
        def get_for_regions(self, db_session, city, country):
            return []

    class EmptyLabourStatsRepository:
        def get_for_regions(self, db_session, city, country):
            return []

    service = InsightService(
        demographics_repository=EmptyDemographicsRepository(),
        spending_repository=EmptySpendingRepository(),
        labour_stats_repository=EmptyLabourStatsRepository(),
    )

    with pytest.raises(HTTPException) as exc_info:
        service.generate_market_summary(
            db_session=None,
            city="Accra",
            country=None,
            tenant_id=uuid4(),
        )

    assert exc_info.value.status_code == 404
