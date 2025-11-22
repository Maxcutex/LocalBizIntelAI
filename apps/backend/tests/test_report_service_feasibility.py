from uuid import uuid4

import pytest
from fastapi import HTTPException

from api.schemas.reports import FeasibilityReportRequest
from services.report_service import ReportService


class FakeJob:
    def __init__(self, job_id: str):
        self.id = job_id
        self.status = "PENDING"


def test_create_feasibility_report_creates_job_and_publishes():
    published_messages = []

    class FakeBillingService:
        def check_report_quota(self, db_session, tenant_id):
            return True

    class FakeJobsRepository:
        def create_pending_job(
            self, db_session, tenant_id, city, country, business_type
        ):
            return FakeJob("job-1")

    class FakePubSubClient:
        def publish_report_job(self, topic, message):
            published_messages.append((topic, message))

    service = ReportService(
        report_jobs_repository=FakeJobsRepository(),
        billing_service=FakeBillingService(),
        pubsub_client=FakePubSubClient(),
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
    class FakeBillingService:
        def check_report_quota(self, db_session, tenant_id):
            return False

    service = ReportService(billing_service=FakeBillingService())

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
