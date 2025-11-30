"""Unit tests for `SpendingEtlJob` happy and failure paths."""

from datetime import datetime, timezone
from typing import Any, cast

import pytest
from sqlalchemy.orm import Session

from api.config import get_settings
from jobs.spending_etl_job import SpendingEtlJob


class DummySession:
    """Minimal session fixture capturing add/flush calls."""

    def __init__(self) -> None:
        self.added: list[Any] = []
        self.flushed = False

    def add(self, obj: Any) -> None:
        self.added.append(obj)

    def flush(self) -> None:
        self.flushed = True


def test_spending_etl_job_happy_path_updates_rows_and_freshness() -> None:
    """Happy path upserts rows, updates freshness, and logs."""

    class FakeSourceClient:
        def fetch_spending(
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
                    "category": "groceries",
                    "avg_monthly_spend": 320.5,
                    "spend_index": 1.02,
                },
                {
                    "geo_id": "accra-2",
                    "country": "GH",
                    "city": "Accra",
                    "category": "dining",
                    "avg_monthly_spend": 180.0,
                    "spend_index": 0.97,
                },
            ]

    class FakeSpendingRepository:
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
            assert dataset_name == "spending"
            assert status == "COMPLETED"
            assert row_count == 2
            assert last_run.tzinfo == timezone.utc
            self.last_call = (dataset_name, status, row_count)

    db_session = DummySession()
    spending_repository = FakeSpendingRepository()
    freshness_repository = FakeDataFreshnessRepository()

    job = SpendingEtlJob(
        spending_repository=spending_repository,
        data_freshness_repository=freshness_repository,
        source_client=FakeSourceClient(),
        settings=get_settings(),
    )

    result = job.run(
        db_session=cast(Session, db_session), country="GH", city="Accra", options={}
    )

    assert result.status == "COMPLETED"
    assert result.row_count == 2
    assert spending_repository.called_with is not None
    assert freshness_repository.last_call is not None
    assert db_session.flushed is True


def test_spending_etl_job_failure_marks_freshness_failed() -> None:
    """Failure path marks freshness FAILED and re-raises."""

    class FailingSourceClient:
        def fetch_spending(
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

    class FakeSpendingRepository:
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
            _ = last_run
            self.last_call = (dataset_name, status, row_count)
            assert status == "FAILED"

    db_session = DummySession()
    freshness_repository = FakeDataFreshnessRepository()

    job = SpendingEtlJob(
        spending_repository=FakeSpendingRepository(),
        data_freshness_repository=freshness_repository,
        source_client=FailingSourceClient(),
        settings=get_settings(),
    )

    with pytest.raises(RuntimeError):
        job.run(
            db_session=cast(Session, db_session), country="GH", city="Accra", options={}
        )

    assert freshness_repository.last_call == ("spending", "FAILED", 0)
