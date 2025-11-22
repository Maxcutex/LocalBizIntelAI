from uuid import uuid4

import pytest
from fastapi import HTTPException

from services.persona_service import PersonaService


class FakeDemographicsRow:
    geo_id = "accra-1"
    population_total = 1000
    median_income = 200
    age_distribution = None


def test_generate_personas_calls_ai_client():
    class FakeDemographicsRepository:
        def get_for_regions(self, db_session, city, country):
            return [FakeDemographicsRow()]

    class EmptyRepository:
        def get_for_regions(self, db_session, city, country):
            return []

    class FakeAiClient:
        def generate_personas(self, input_payload):
            assert input_payload["city"] == "Accra"
            return {"headline": "ai", "personas": []}

    service = PersonaService(
        demographics_repository=FakeDemographicsRepository(),
        spending_repository=EmptyRepository(),
        labour_stats_repository=EmptyRepository(),
        ai_engine_client=FakeAiClient(),
    )

    result = service.generate_personas(
        db_session=None,
        city="Accra",
        country=None,
        geo_ids=None,
        business_type=None,
        tenant_id=uuid4(),
    )

    assert result["personas"]["headline"] == "ai"


def test_generate_personas_raises_404_when_no_data():
    class EmptyRepository:
        def get_for_regions(self, db_session, city, country):
            return []

    service = PersonaService(
        demographics_repository=EmptyRepository(),
        spending_repository=EmptyRepository(),
        labour_stats_repository=EmptyRepository(),
    )

    with pytest.raises(HTTPException) as exc_info:
        service.generate_personas(
            db_session=None,
            city="Accra",
            country=None,
            geo_ids=None,
            business_type=None,
            tenant_id=uuid4(),
        )

    assert exc_info.value.status_code == 404
