"""Unit tests for `InsightService.find_opportunities`."""

from uuid import uuid4

import pytest
from fastapi import HTTPException

from services.dependencies import InsightServiceDependencies
from services.insight_service import InsightService


class FakeOpportunityRow:
    """Row-like fixture representing an opportunity score ORM row."""

    def __init__(self, geo_id: str, composite_score: float, competition_score: float):
        """Populate fixture fields."""
        self.geo_id = geo_id
        self.country = "GH"
        self.city = "Accra"
        self.business_type = "retail"
        self.demand_score = 0.8
        self.supply_score = 0.4
        self.competition_score = competition_score
        self.composite_score = composite_score
        self.calculated_at = None


def test_find_opportunities_applies_constraints_and_ranks():
    """Constraints filter regions and results are ranked by score."""

    class FakeOpportunityRepository:
        """Fake opportunity repository returning two rows."""

        def list_by_city_and_business_type(
            self, _db_session, _city, _country, _business_type
        ):
            """Return canned rows."""
            return [
                FakeOpportunityRow("accra-1", 0.9, 0.2),
                FakeOpportunityRow("accra-2", 0.4, 0.1),
            ]

    class FakeAiClient:
        """Fake AI client returning canned commentary."""

        def generate_opportunity_commentary(self, ranked_regions):
            """Return commentary for ranked regions."""
            assert len(ranked_regions) == 1
            return {"commentary": "ai"}

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

    service = InsightService(
        InsightServiceDependencies(
            demographics_repository=DummyDemographicsRepository(),
            spending_repository=DummySpendingRepository(),
            labour_stats_repository=DummyLabourStatsRepository(),
            opportunity_scores_repository=FakeOpportunityRepository(),
            ai_engine_client=FakeAiClient(),
        )
    )

    result = service.find_opportunities(
        db_session=None,
        city="Accra",
        business_type="retail",
        constraints={"min_composite_score": 0.5},
        country=None,
        tenant_id=uuid4(),
    )

    assert [r["geo_id"] for r in result["opportunities"]] == ["accra-1"]
    assert result["ai_commentary"]["commentary"] == "ai"
    assert "stats_used" in result


def test_find_opportunities_raises_404_when_empty():
    """Empty opportunity list raises 404."""

    class EmptyOpportunityRepository:
        """Fake opportunity repository returning no rows."""

        def list_by_city_and_business_type(
            self, _db_session, _city, _country, _business_type
        ):
            """Return empty list."""
            return []

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

    class DummyAiClient:
        """Stub AI client (unused)."""

        def generate_opportunity_commentary(self, ranked_regions):
            """Return placeholder commentary."""
            _ = ranked_regions
            return {"commentary": "unused"}

    service = InsightService(
        InsightServiceDependencies(
            demographics_repository=DummyDemographicsRepository(),
            spending_repository=DummySpendingRepository(),
            labour_stats_repository=DummyLabourStatsRepository(),
            opportunity_scores_repository=EmptyOpportunityRepository(),
            ai_engine_client=DummyAiClient(),
        )
    )

    with pytest.raises(HTTPException) as exc_info:
        service.find_opportunities(
            db_session=None,
            city="Accra",
            business_type=None,
            constraints=None,
            country=None,
            tenant_id=uuid4(),
        )

    assert exc_info.value.status_code == 404


def test_find_opportunities_sorts_and_falls_back_when_ai_fails():
    """AI failures do not prevent sorted results from returning."""

    class FakeOpportunityRepository:
        """Fake opportunity repository returning two rows."""

        def list_by_city_and_business_type(
            self, _db_session, _city, _country, _business_type
        ):
            """Return canned rows."""
            return [
                FakeOpportunityRow("accra-low", 0.3, 0.2),
                FakeOpportunityRow("accra-high", 0.9, 0.5),
            ]

    class FailingAiClient:
        """Fake AI client that always errors."""

        def generate_opportunity_commentary(self, ranked_regions):
            """Raise to simulate AI outage."""
            _ = ranked_regions
            raise RuntimeError("boom")

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

    service = InsightService(
        InsightServiceDependencies(
            demographics_repository=DummyDemographicsRepository(),
            spending_repository=DummySpendingRepository(),
            labour_stats_repository=DummyLabourStatsRepository(),
            opportunity_scores_repository=FakeOpportunityRepository(),
            ai_engine_client=FailingAiClient(),
        )
    )

    result = service.find_opportunities(
        db_session=None,
        city="Accra",
        business_type="retail",
        constraints=None,
        country=None,
        tenant_id=uuid4(),
    )

    assert [r["geo_id"] for r in result["opportunities"]] == [
        "accra-high",
        "accra-low",
    ]
    assert "commentary" in result["ai_commentary"]
