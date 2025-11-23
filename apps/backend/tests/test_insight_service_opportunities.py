from uuid import uuid4

import pytest
from fastapi import HTTPException

from services.insight_service import InsightService


class FakeOpportunityRow:
    def __init__(self, geo_id: str, composite_score: float, competition_score: float):
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
    class FakeOpportunityRepository:
        def list_by_city_and_business_type(
            self, db_session, city, country, business_type
        ):
            return [
                FakeOpportunityRow("accra-1", 0.9, 0.2),
                FakeOpportunityRow("accra-2", 0.4, 0.1),
            ]

    class FakeAiClient:
        def generate_opportunity_commentary(self, ranked_regions):
            assert len(ranked_regions) == 1
            return {"commentary": "ai"}

    service = InsightService(
        opportunity_scores_repository=FakeOpportunityRepository(),
        ai_engine_client=FakeAiClient(),
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


def test_find_opportunities_raises_404_when_empty():
    class EmptyOpportunityRepository:
        def list_by_city_and_business_type(
            self, db_session, city, country, business_type
        ):
            return []

    service = InsightService(opportunity_scores_repository=EmptyOpportunityRepository())

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
    class FakeOpportunityRepository:
        def list_by_city_and_business_type(
            self, db_session, city, country, business_type
        ):
            return [
                FakeOpportunityRow("accra-low", 0.3, 0.2),
                FakeOpportunityRow("accra-high", 0.9, 0.5),
            ]

    class FailingAiClient:
        def generate_opportunity_commentary(self, ranked_regions):
            raise RuntimeError("boom")

    service = InsightService(
        opportunity_scores_repository=FakeOpportunityRepository(),
        ai_engine_client=FailingAiClient(),
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
