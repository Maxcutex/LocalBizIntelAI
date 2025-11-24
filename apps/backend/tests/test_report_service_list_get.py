"""Unit tests for `ReportService` list/get behaviors."""

from uuid import uuid4

import pytest
from fastapi import HTTPException

from services.dependencies import ReportServiceDependencies
from services.report_service import ReportService


class FakeJob:
    """Minimal report job fixture."""

    def __init__(self, job_id):
        """Create fixture with id attribute."""
        self.id = job_id


def test_list_reports_returns_jobs_for_tenant():
    """Listing reports returns repository results for tenant."""
    tenant_id = uuid4()
    jobs = [FakeJob(uuid4())]

    class FakeRepo:
        """Fake report jobs repository."""

        def list_by_tenant(self, _db_session, requested_tenant_id):
            """Return canned jobs."""
            assert requested_tenant_id == tenant_id
            return jobs

    class DummyBillingService:
        """Stub billing service."""

        def check_report_quota(self, _db_session, _tenant_id):
            """Not used in this test."""
            raise AssertionError("not used")

    class DummyPubSubClient:
        """Stub Pub/Sub client."""

        def publish_report_job(self, _topic, _message):
            """Not used in this test."""
            raise AssertionError("not used")

    service = ReportService(
        ReportServiceDependencies(
            report_jobs_repository=FakeRepo(),
            billing_service=DummyBillingService(),
            pubsub_client=DummyPubSubClient(),
        )
    )
    result = service.list_reports(db_session=None, tenant_id=tenant_id)

    assert result == jobs


def test_get_report_raises_404_when_missing():
    """Missing report raises 404."""

    class FakeRepo:
        """Fake report jobs repository returning no report."""

        def get_for_tenant(self, _db_session, _report_id, _tenant_id):
            """Return None for any lookup."""
            return None

    class DummyBillingService:
        """Stub billing service."""

        def check_report_quota(self, _db_session, _tenant_id):
            """Not used in this test."""
            raise AssertionError("not used")

    class DummyPubSubClient:
        """Stub Pub/Sub client."""

        def publish_report_job(self, _topic, _message):
            """Not used in this test."""
            raise AssertionError("not used")

    service = ReportService(
        ReportServiceDependencies(
            report_jobs_repository=FakeRepo(),
            billing_service=DummyBillingService(),
            pubsub_client=DummyPubSubClient(),
        )
    )

    with pytest.raises(HTTPException) as exc_info:
        service.get_report(db_session=None, report_id=uuid4(), tenant_id=uuid4())

    assert exc_info.value.status_code == 404
