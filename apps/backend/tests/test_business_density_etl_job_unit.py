"""Unit tests for `BusinessDensityEtlJob` and Overpass source client."""

from datetime import datetime, timezone
from typing import Any, cast

import httpx
import pytest

from api.config import get_settings
from jobs.business_density_etl_job import (
    BusinessDensityEtlJob,
    OverpassBusinessDensitySourceClient,
)


class DummySession:
    """Minimal session fixture capturing add/flush calls."""

    def __init__(self) -> None:
        self.added: list[Any] = []
        self.flushed = False

    def add(self, obj: Any) -> None:
        self.added.append(obj)

    def flush(self) -> None:
        self.flushed = True


def test_business_density_etl_job_happy_path_updates_rows_and_freshness() -> None:
    """Happy path upserts rows, updates freshness, and logs."""

    class FakeSourceClient:
        def fetch_business_density(
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
                    "geo_id": "accra-citywide",
                    "country": "GH",
                    "city": "Accra",
                    "business_type": "cafes",
                    "count": 10,
                },
                {
                    "geo_id": "accra-citywide",
                    "country": "GH",
                    "city": "Accra",
                    "business_type": "gyms",
                    "count": 3,
                },
            ]

    class FakeBusinessDensityRepository:
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
            assert dataset_name == "business_density"
            assert status == "COMPLETED"
            assert row_count == 2
            assert last_run.tzinfo == timezone.utc
            self.last_call = (dataset_name, status, row_count)

    db_session = DummySession()
    density_repository = FakeBusinessDensityRepository()
    freshness_repository = FakeDataFreshnessRepository()

    job = BusinessDensityEtlJob(
        business_density_repository=density_repository,
        data_freshness_repository=freshness_repository,
        source_client=FakeSourceClient(),
        settings=get_settings(),
    )

    result = job.run(db_session=db_session, country="GH", city="Accra", options={})

    assert result.status == "COMPLETED"
    assert result.row_count == 2
    assert density_repository.called_with is not None
    assert freshness_repository.last_call is not None
    assert db_session.flushed is True


def test_business_density_etl_job_failure_marks_freshness_failed() -> None:
    """Failure path marks freshness FAILED and re-raises."""

    class FailingSourceClient:
        def fetch_business_density(
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

    class FakeBusinessDensityRepository:
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

    job = BusinessDensityEtlJob(
        business_density_repository=FakeBusinessDensityRepository(),
        data_freshness_repository=freshness_repository,
        source_client=FailingSourceClient(),
        settings=get_settings(),
    )

    with pytest.raises(RuntimeError):
        job.run(db_session=db_session, country="GH", city="Accra", options={})

    assert freshness_repository.last_call == ("business_density", "FAILED", 0)


def test_overpass_source_client_builds_rows_from_http_response() -> None:
    """Overpass source client converts elements into per-type rows."""

    class FakeResponse:
        def __init__(self, payload: dict[str, Any]) -> None:
            self._payload = payload

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, Any]:
            return self._payload

    class FakeHttpClient:
        def __init__(self) -> None:
            self.calls: list[bytes] = []
            self._payloads: list[dict[str, Any]] = [
                {"elements": [{"id": 1, "lat": 1.0, "lon": 2.0}]},
                {"elements": [{"id": 2, "lat": 3.0, "lon": 4.0}]},
                {"elements": []},
            ]

        def post(self, _url: str, data: bytes) -> FakeResponse:
            self.calls.append(data)
            payload = self._payloads[len(self.calls) - 1]
            return FakeResponse(payload)

    fake_http_client = FakeHttpClient()
    source_client = OverpassBusinessDensitySourceClient(
        overpass_endpoint="http://example.test/overpass",
        http_client=cast(httpx.Client, fake_http_client),
    )

    rows = source_client.fetch_business_density(
        country="CA",
        city="Toronto",
        options={},
        settings=get_settings(),
    )

    assert len(fake_http_client.calls) == 3
    assert [row["business_type"] for row in rows] == [
        "cafes",
        "restaurants",
        "gyms",
    ]
    assert [row["count"] for row in rows] == [1, 1, 0]
