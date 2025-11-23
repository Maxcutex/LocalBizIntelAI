from uuid import uuid4

import pytest
from fastapi import HTTPException

from services.report_service import ReportService


class FakeJob:
    def __init__(self, job_id):
        self.id = job_id


def test_list_reports_returns_jobs_for_tenant():
    tenant_id = uuid4()
    jobs = [FakeJob(uuid4())]

    class FakeRepo:
        def list_by_tenant(self, db_session, requested_tenant_id):
            assert requested_tenant_id == tenant_id
            return jobs

    class DummyBillingService:
        def check_report_quota(self, db_session, tenant_id):
            raise AssertionError("not used")

    class DummyPubSubClient:
        def publish_report_job(self, topic, message):
            raise AssertionError("not used")

    service = ReportService(
        report_jobs_repository=FakeRepo(),
        billing_service=DummyBillingService(),
        pubsub_client=DummyPubSubClient(),
    )
    result = service.list_reports(db_session=None, tenant_id=tenant_id)

    assert result == jobs


def test_get_report_raises_404_when_missing():
    class FakeRepo:
        def get_for_tenant(self, db_session, report_id, tenant_id):
            return None

    class DummyBillingService:
        def check_report_quota(self, db_session, tenant_id):
            raise AssertionError("not used")

    class DummyPubSubClient:
        def publish_report_job(self, topic, message):
            raise AssertionError("not used")

    service = ReportService(
        report_jobs_repository=FakeRepo(),
        billing_service=DummyBillingService(),
        pubsub_client=DummyPubSubClient(),
    )

    with pytest.raises(HTTPException) as exc_info:
        service.get_report(db_session=None, report_id=uuid4(), tenant_id=uuid4())

    assert exc_info.value.status_code == 404
