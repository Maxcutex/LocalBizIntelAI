"""Unit tests for `DemographicsEtlJob` happy and failure paths."""

from datetime import datetime, timezone

import pytest

from jobs.demographics_etl_job import DemographicsEtlJob


class DummySession:
    """Minimal session fixture capturing add/flush calls."""

    def __init__(self):
        """Initialize fixture state."""
        self.added = []
        self.flushed = False

    def add(self, obj):
        """Record added objects."""
        self.added.append(obj)

    def flush(self):
        """Mark flush as called."""
        self.flushed = True


def test_demographics_etl_job_happy_path_updates_rows_and_freshness():
    """Happy path upserts rows, updates freshness, and logs."""

    class FakeSourceClient:
        """Fake source returning deterministic demographics rows."""

        def fetch_demographics(self, *, _country, _city, _options, _settings):
            """Return canned demographics rows."""
            return [
                {
                    "geo_id": "accra-1",
                    "country": "GH",
                    "city": "Accra",
                    "population_total": 100,
                    "median_income": 10,
                },
                {
                    "geo_id": "accra-2",
                    "country": "GH",
                    "city": "Accra",
                    "population_total": 200,
                    "median_income": 20,
                },
            ]

    class FakeDemographicsRepository:
        """Fake demographics repository asserting on upsert."""

        def __init__(self):
            """Initialize call-capture state."""
            self.called_with = None

        def upsert_many(self, db_session, rows, last_updated):
            """Capture input and return affected row count."""
            assert isinstance(last_updated, datetime)
            self.called_with = (db_session, rows)
            return len(rows)

    class FakeDataFreshnessRepository:
        """Fake data freshness repository asserting on upsert."""

        def __init__(self):
            """Initialize call-capture state."""
            self.last_call = None

        def upsert_status(self, _db_session, dataset_name, last_run, row_count, status):
            """Capture status update call."""
            assert dataset_name == "demographics"
            assert status == "COMPLETED"
            assert row_count == 2
            assert last_run.tzinfo == timezone.utc
            self.last_call = (dataset_name, status, row_count)

    db_session = DummySession()
    demographics_repository = FakeDemographicsRepository()
    data_freshness_repository = FakeDataFreshnessRepository()

    job = DemographicsEtlJob(
        demographics_repository=demographics_repository,
        data_freshness_repository=data_freshness_repository,
        source_client=FakeSourceClient(),
    )

    result = job.run(db_session=db_session, country="GH", city="Accra")

    assert result.status == "COMPLETED"
    assert result.row_count == 2
    assert demographics_repository.called_with is not None
    assert data_freshness_repository.last_call is not None
    assert db_session.flushed is True


def test_demographics_etl_job_failure_marks_freshness_failed():
    """Failure path marks freshness FAILED and re-raises."""

    class FailingSourceClient:
        """Fake source that raises to simulate provider failure."""

        def fetch_demographics(self, *, _country, _city, _options, _settings):
            """Raise to simulate provider error."""
            raise RuntimeError("boom")

    class FakeDemographicsRepository:
        """Fake demographics repository (should not be called)."""

        def upsert_many(self, _db_session, _rows, _last_updated):
            """Not used in this test."""
            raise AssertionError("should not be called")

    class FakeDataFreshnessRepository:
        """Fake data freshness repository capturing failure status."""

        def __init__(self):
            """Initialize call-capture state."""
            self.last_call = None

        def upsert_status(self, db_session, dataset_name, last_run, row_count, status):
            """Capture failure marker call."""
            _ = db_session
            _ = dataset_name
            _ = last_run
            self.last_call = (dataset_name, status, row_count)
            assert status == "FAILED"

    db_session = DummySession()
    data_freshness_repository = FakeDataFreshnessRepository()

    job = DemographicsEtlJob(
        demographics_repository=FakeDemographicsRepository(),
        data_freshness_repository=data_freshness_repository,
        source_client=FailingSourceClient(),
    )

    with pytest.raises(RuntimeError):
        job.run(db_session=db_session, country="GH", city="Accra")

    assert data_freshness_repository.last_call == ("demographics", "FAILED", 0)
