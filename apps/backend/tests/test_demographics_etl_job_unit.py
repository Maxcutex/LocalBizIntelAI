from datetime import datetime, timezone

import pytest

from jobs.demographics_etl_job import DemographicsEtlJob


class DummySession:
    def __init__(self):
        self.added = []
        self.flushed = False

    def add(self, obj):
        self.added.append(obj)

    def flush(self):
        self.flushed = True


def test_demographics_etl_job_happy_path_updates_rows_and_freshness():
    class FakeSourceClient:
        def fetch_demographics(self, *, country, city, options, settings):
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
        def __init__(self):
            self.called_with = None

        def upsert_many(self, db_session, rows, last_updated):
            assert isinstance(last_updated, datetime)
            self.called_with = (db_session, rows)
            return len(rows)

    class FakeDataFreshnessRepository:
        def __init__(self):
            self.last_call = None

        def upsert_status(self, db_session, dataset_name, last_run, row_count, status):
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
    class FailingSourceClient:
        def fetch_demographics(self, *, country, city, options, settings):
            raise RuntimeError("boom")

    class FakeDemographicsRepository:
        def upsert_many(self, db_session, rows, last_updated):
            raise AssertionError("should not be called")

    class FakeDataFreshnessRepository:
        def __init__(self):
            self.last_call = None

        def upsert_status(self, db_session, dataset_name, last_run, row_count, status):
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
