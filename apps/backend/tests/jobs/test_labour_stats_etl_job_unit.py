"""Unit tests for `LabourStatsEtlJob` happy and failure paths."""

from datetime import datetime, timezone
from typing import Any, cast

import pytest
from sqlalchemy.orm import Session

from api.config import get_settings
from jobs.labour_stats_etl_job import LabourStatsEtlJob


class DummySession:
    """Minimal session fixture capturing add/flush calls."""

    def __init__(self) -> None:
        self.added: list[Any] = []
        self.flushed = False

    def add(self, obj: Any) -> None:
        self.added.append(obj)

    def flush(self) -> None:
        self.flushed = True


def test_labour_stats_etl_job_happy_path_updates_rows_and_freshness() -> None:
    """Happy path upserts rows, updates freshness, and logs."""

    class FakeSourceClient:
        def fetch_labour_stats(
            self,
            *,
            country: str | None,
            city: str | None,
            options: dict[str, Any],
            settings,
        ) -> list[dict[str, Any]]:
            _ = country
            _ = city
            _ = options
            _ = settings
            return [
                {
                    "geo_id": "accra-1",
                    "country": "GH",
                    "city": "Accra",
                    "unemployment_rate": 5.5,
                    "job_openings": 1200,
                    "median_salary": 700,
                    "labour_force_participation": 62.1,
                },
                {
                    "geo_id": "accra-2",
                    "country": "GH",
                    "city": "Accra",
                    "unemployment_rate": 6.1,
                    "job_openings": 900,
                    "median_salary": 650,
                    "labour_force_participation": 60.9,
                },
            ]

    class FakeLabourStatsRepository:
        def __init__(self) -> None:
            self.called_with: tuple[Any, Any] | None = None

        def upsert_many(
            self, db_session: Any, rows: list[dict[str, Any]], last_updated: datetime
        ) -> int:
            assert isinstance(last_updated, datetime)
            self.called_with = (db_session, rows)
            return len(rows)

    class FakeDataFreshnessRepository:
        def __init__(self) -> None:
            self.last_call: tuple[str, str, int] | None = None

        def upsert_status(
            self,
            *,
            db_session: Any,
            dataset_name: str,
            last_run: datetime,
            row_count: int,
            status: str,
        ) -> None:
            _ = db_session
            assert dataset_name == "labour_stats"
            assert status == "COMPLETED"
            assert row_count == 2
            assert last_run.tzinfo == timezone.utc
            self.last_call = (dataset_name, status, row_count)

    db_session = DummySession()
    labour_repository = FakeLabourStatsRepository()
    freshness_repository = FakeDataFreshnessRepository()

    job = LabourStatsEtlJob(
        labour_stats_repository=labour_repository,
        data_freshness_repository=freshness_repository,
        source_client=FakeSourceClient(),
        settings=get_settings(),
    )

    result = job.run(
        db_session=cast(Session, db_session), country="GH", city="Accra", options={}
    )

    assert result.status == "COMPLETED"
    assert result.row_count == 2
    assert labour_repository.called_with is not None
    assert freshness_repository.last_call is not None
    assert db_session.flushed is True


def test_labour_stats_etl_job_failure_marks_freshness_failed() -> None:
    """Failure path marks freshness FAILED and re-raises."""

    class FailingSourceClient:
        def fetch_labour_stats(
            self,
            *,
            country: str | None,
            city: str | None,
            options: dict[str, Any],
            settings,
        ) -> list[dict[str, Any]]:
            _ = country
            _ = city
            _ = options
            _ = settings
            raise RuntimeError("boom")

    class FakeLabourStatsRepository:
        def upsert_many(self, *_args: Any, **_kwargs: Any) -> int:
            raise AssertionError("should not be called")

    class FakeDataFreshnessRepository:
        def __init__(self) -> None:
            self.last_call: tuple[str, str, int] | None = None

        def upsert_status(
            self,
            *,
            db_session: Any,
            dataset_name: str,
            last_run: datetime,
            row_count: int,
            status: str,
        ) -> None:
            _ = db_session
            _ = dataset_name
            _ = last_run
            self.last_call = (dataset_name, status, row_count)
            assert status == "FAILED"

    db_session = DummySession()
    freshness_repository = FakeDataFreshnessRepository()

    job = LabourStatsEtlJob(
        labour_stats_repository=FakeLabourStatsRepository(),
        data_freshness_repository=freshness_repository,
        source_client=FailingSourceClient(),
        settings=get_settings(),
    )

    with pytest.raises(RuntimeError):
        job.run(
            db_session=cast(Session, db_session), country="GH", city="Accra", options={}
        )

    assert freshness_repository.last_call == ("labour_stats", "FAILED", 0)
