from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, cast

import pytest
from sqlalchemy.orm import Session

from api.config import Settings
from jobs.rebuild_embeddings_job import RebuildEmbeddingsJob


class DummySession:
    def __init__(self) -> None:
        self.added: list[Any] = []
        self.flushed = False

    def add(self, obj: Any) -> None:
        self.added.append(obj)

    def flush(self) -> None:
        self.flushed = True


@dataclass
class DemoRow:
    geo_id: str
    population_total: int | None = None
    median_income: Any | None = None
    unemployment_rate: Any | None = None
    median_salary: Any | None = None
    job_openings: int | None = None
    category: str | None = None
    avg_monthly_spend: Any | None = None
    spend_index: Any | None = None
    business_type: str | None = None
    count: int | None = None
    density_score: Any | None = None


@contextmanager
def _disable_dotenv_for_settings() -> Any:
    old_env_file = Settings.model_config.get("env_file")
    Settings.model_config["env_file"] = None
    try:
        yield
    finally:
        Settings.model_config["env_file"] = old_env_file


def test_rebuild_embeddings_job_happy_path_upserts_vectors_and_logs() -> None:
    with _disable_dotenv_for_settings():
        settings = Settings(openai_embedding_dimensions=8)

    class FakeDemographicsRepo:
        def get_for_regions(self, _db, _city, _country):
            return [
                DemoRow(
                    geo_id="accra-central", population_total=100, median_income=500
                ),
                DemoRow(geo_id="accra-north", population_total=200, median_income=600),
            ]

    class FakeSpendingRepo:
        def get_for_regions(self, _db, _city, _country):
            return [
                DemoRow(
                    geo_id="accra-central",
                    category="groceries",
                    avg_monthly_spend=10,
                    spend_index=1.1,
                )
            ]

    class FakeLabourRepo:
        def get_for_regions(self, _db, _city, _country):
            return [
                DemoRow(
                    geo_id="accra-central",
                    unemployment_rate=5.0,
                    median_salary=1000,
                    job_openings=50,
                )
            ]

    class FakeDensityRepo:
        def list_by_city_and_type(self, _db, _city, _country, business_type=None):
            _ = business_type
            return [DemoRow(geo_id="accra-central", business_type="cafe", count=3)]

    class FakeVectorRepo:
        def __init__(self) -> None:
            self.rows: list[dict[str, Any]] | None = None

        def upsert_many(
            self, _db, rows: list[dict[str, Any]], created_at: datetime
        ) -> int:
            assert created_at.tzinfo == timezone.utc
            self.rows = rows
            return len(rows)

    class FakeEmbeddingClient:
        def embed_texts(self, texts: list[str]) -> list[list[float]]:
            return [[0.0] * settings.openai_embedding_dimensions for _ in texts]

    db = DummySession()
    vector_repo = FakeVectorRepo()

    job = RebuildEmbeddingsJob(
        demographics_repository=FakeDemographicsRepo(),
        spending_repository=FakeSpendingRepo(),
        labour_stats_repository=FakeLabourRepo(),
        business_density_repository=FakeDensityRepo(),
        vector_insights_repository=vector_repo,
        embedding_client=FakeEmbeddingClient(),
        settings=settings,
    )

    result = job.run(
        db_session=cast(Session, db),
        country="GH",
        city="Accra",
        regions=None,
        options={},
        tenant_id=None,
    )

    assert result.status == "COMPLETED"
    assert result.row_count == 2
    assert result.region_count == 2
    assert db.flushed is True
    assert vector_repo.rows is not None
    assert {row["geo_id"] for row in vector_repo.rows} == {
        "accra-central",
        "accra-north",
    }


def test_rebuild_embeddings_job_dimension_mismatch_fails_and_logs_failed() -> None:
    with _disable_dotenv_for_settings():
        settings = Settings(openai_embedding_dimensions=8)

    class EmptyRepo:
        def get_for_regions(self, *_a, **_kw):
            return [DemoRow(geo_id="accra-central")]

        def list_by_city_and_type(self, *_a, **_kw):
            return []

    class FakeVectorRepo:
        def upsert_many(self, *_a, **_kw) -> int:
            raise AssertionError("should not be called")

    class BadEmbeddingClient:
        def embed_texts(self, texts: list[str]) -> list[list[float]]:
            return [[0.0] * (settings.openai_embedding_dimensions - 1) for _ in texts]

    db = DummySession()
    job = RebuildEmbeddingsJob(
        demographics_repository=EmptyRepo(),
        spending_repository=EmptyRepo(),
        labour_stats_repository=EmptyRepo(),
        business_density_repository=EmptyRepo(),
        vector_insights_repository=FakeVectorRepo(),
        embedding_client=BadEmbeddingClient(),
        settings=settings,
    )

    with pytest.raises(ValueError):
        job.run(
            db_session=cast(Session, db),
            country="GH",
            city="Accra",
            regions=None,
            options={},
            tenant_id=None,
        )

    assert db.flushed is True
