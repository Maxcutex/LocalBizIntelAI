"""Unit tests for `InsightService.generate_market_summary`."""

from uuid import uuid4

import pytest
from fastapi import HTTPException

from services.dependencies import InsightServiceDependencies
from services.insight_service import InsightService


def test_generate_market_summary_merges_stats_and_ai():
    """Market summary merges DB stats with AI output."""

    class FakeDemographicsRepository:
        """Fake demographics repository."""

        def get_for_regions(self, _db_session, _city, _country):
            """Return one demographics row."""

            class FakeRow:
                """Row-like fixture for demographics."""

                geo_id = "accra-1"
                population_total = 1000
                median_income = 200

            return [FakeRow()]

    class FakeSpendingRepository:
        """Fake spending repository."""

        def get_for_regions(self, _db_session, _city, _country):
            """Return no spending rows."""
            return []

    class FakeLabourStatsRepository:
        """Fake labour stats repository."""

        def get_for_regions(self, _db_session, _city, _country):
            """Return no labour rows."""
            return []

    class FakeAiClient:
        """Fake AI client."""

        def generate_market_summary(self, payload):
            """Return canned AI summary."""
            assert payload["city"] == "Accra"
            return {"summary": "ai"}

    class DummyOpportunityRepository:
        """Stub opportunity scores repository (unused in this test)."""

        def list_by_city_and_business_type(
            self, _db_session, _city, _country, _business_type
        ):
            """Not used in this test."""
            raise AssertionError("not used")

    service = InsightService(
        InsightServiceDependencies(
            demographics_repository=FakeDemographicsRepository(),
            spending_repository=FakeSpendingRepository(),
            labour_stats_repository=FakeLabourStatsRepository(),
            opportunity_scores_repository=DummyOpportunityRepository(),
            ai_engine_client=FakeAiClient(),
        )
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
    """No demographics/spending/labour data yields 404."""

    class EmptyDemographicsRepository:
        """Empty demographics repository."""

        def get_for_regions(self, _db_session, _city, _country):
            """Return empty list."""
            return []

    class EmptySpendingRepository:
        """Empty spending repository."""

        def get_for_regions(self, _db_session, _city, _country):
            """Return empty list."""
            return []

    class EmptyLabourStatsRepository:
        """Empty labour stats repository."""

        def get_for_regions(self, _db_session, _city, _country):
            """Return empty list."""
            return []

    class DummyOpportunityRepository:
        """Stub opportunity scores repository (unused in this test)."""

        def list_by_city_and_business_type(
            self, _db_session, _city, _country, _business_type
        ):
            """Not used in this test."""
            raise AssertionError("not used")

    class DummyAiClient:
        """Stub AI client."""

        def generate_market_summary(self, _payload):
            """Not used in this test."""
            raise AssertionError("not used")

    service = InsightService(
        InsightServiceDependencies(
            demographics_repository=EmptyDemographicsRepository(),
            spending_repository=EmptySpendingRepository(),
            labour_stats_repository=EmptyLabourStatsRepository(),
            opportunity_scores_repository=DummyOpportunityRepository(),
            ai_engine_client=DummyAiClient(),
        )
    )

    with pytest.raises(HTTPException) as exc_info:
        service.generate_market_summary(
            db_session=None,
            city="Accra",
            country=None,
            tenant_id=uuid4(),
        )

    assert exc_info.value.status_code == 404
