"""Unit tests for `ReportService.create_feasibility_report`."""

from uuid import uuid4

import pytest
from fastapi import HTTPException

from api.schemas.reports import FeasibilityReportRequest
from services.dependencies import ReportServiceDependencies
from services.report_service import ReportService


class FakeJob:
    """Minimal report job fixture."""

    def __init__(self, job_id: str):
        """Create fixture with id/status."""
        self.id = job_id
        self.status = "PENDING"


def test_create_feasibility_report_creates_job_and_publishes():
    """Happy path creates job and publishes a Pub/Sub message."""
    published_messages = []

    class FakeBillingService:
        """Fake billing service allowing quota."""

        def check_report_quota(self, _db_session, _tenant_id):
            """Return True to allow report creation."""
            return True

    class FakeJobsRepository:
        """Fake report jobs repository returning a pending job."""

        def create_pending_job(
            self, _db_session, _tenant_id, _city, _country, _business_type
        ):
            """Return a canned pending job."""
            return FakeJob("job-1")

    class FakePubSubClient:
        """Fake Pub/Sub client capturing published messages."""

        def publish_report_job(self, topic, message):
            """Append published message."""
            published_messages.append((topic, message))

    service = ReportService(
        ReportServiceDependencies(
            report_jobs_repository=FakeJobsRepository(),
            billing_service=FakeBillingService(),
            pubsub_client=FakePubSubClient(),
        )
    )

    result = service.create_feasibility_report(
        db_session=None,
        request=FeasibilityReportRequest(
            city="Accra", country="GH", business_type="retail"
        ),
        tenant_id=uuid4(),
        user_id=uuid4(),
    )

    assert result["status"] == "PENDING"
    assert len(published_messages) == 1


def test_create_feasibility_report_raises_when_quota_exceeded():
    """Quota exceeded raises HTTP 402 and does not publish."""

    class FakeBillingService:
        """Fake billing service denying quota."""

        def check_report_quota(self, _db_session, _tenant_id):
            """Return False to deny report creation."""
            return False

    class DummyJobsRepository:
        """Stub report jobs repository (unused)."""

        def create_pending_job(
            self, _db_session, _tenant_id, _city, _country, _business_type
        ):
            """Not used in this test."""
            raise AssertionError("should not be called")

    class DummyPubSubClient:
        """Stub Pub/Sub client (unused)."""

        def publish_report_job(self, _topic, _message):
            """Not used in this test."""
            raise AssertionError("should not be called")

    service = ReportService(
        ReportServiceDependencies(
            report_jobs_repository=DummyJobsRepository(),
            billing_service=FakeBillingService(),
            pubsub_client=DummyPubSubClient(),
        )
    )

    with pytest.raises(HTTPException) as exc_info:
        service.create_feasibility_report(
            db_session=None,
            request=FeasibilityReportRequest(
                city="Accra", country="GH", business_type="retail"
            ),
            tenant_id=uuid4(),
            user_id=uuid4(),
        )

    assert exc_info.value.status_code == 402
