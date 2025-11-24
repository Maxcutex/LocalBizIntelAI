"""Unit tests for `PersonaService.generate_personas`."""

from uuid import uuid4

import pytest
from fastapi import HTTPException

from services.dependencies import PersonaServiceDependencies
from services.persona_service import PersonaService


class FakeDemographicsRow:
    """Row-like fixture representing a demographics ORM row."""

    geo_id = "accra-1"
    population_total = 1000
    median_income = 200
    age_distribution = None


def test_generate_personas_calls_ai_client():
    """Service calls AI client and returns personas payload."""

    class FakeDemographicsRepository:
        """Fake demographics repository returning one row."""

        def get_for_regions(self, _db_session, _city, _country):
            """Return canned demographics rows."""
            return [FakeDemographicsRow()]

    class EmptyRepository:
        """Stub repository returning no rows."""

        def get_for_regions(self, _db_session, _city, _country):
            """Return empty list."""
            return []

    class FakeAiClient:
        """Fake AI client asserting on input payload."""

        def generate_personas(self, input_payload):
            """Return canned personas."""
            assert input_payload["city"] == "Accra"
            return {"headline": "ai", "personas": []}

    service = PersonaService(
        PersonaServiceDependencies(
            demographics_repository=FakeDemographicsRepository(),
            spending_repository=EmptyRepository(),
            labour_stats_repository=EmptyRepository(),
            ai_engine_client=FakeAiClient(),
        )
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
    """Empty datasets raise 404."""

    class EmptyRepository:
        """Stub repository returning no rows."""

        def get_for_regions(self, _db_session, _city, _country):
            """Return empty list."""
            return []

    class DummyAiClient:
        """Stub AI client (unused)."""

        def generate_personas(self, _input_payload):
            """Return placeholder personas."""
            return {"headline": "unused", "personas": []}

    service = PersonaService(
        PersonaServiceDependencies(
            demographics_repository=EmptyRepository(),
            spending_repository=EmptyRepository(),
            labour_stats_repository=EmptyRepository(),
            ai_engine_client=DummyAiClient(),
        )
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
