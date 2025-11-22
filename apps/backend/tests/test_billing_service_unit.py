from uuid import uuid4

import pytest
from fastapi import HTTPException

from services.billing_service import BillingService


def test_get_plan_and_usage_returns_none_plan_when_no_account():
    expected_usage = {"reports_this_month": 2}

    class FakeBillingRepository:
        def get_billing_account(self, db_session, tenant_id):
            return None

    class FakeUsageRepository:
        def get_current_usage(self, db_session, tenant_id):
            assert tenant_id is not None
            return expected_usage

    service = BillingService(
        billing_repository=FakeBillingRepository(),
        usage_repository=FakeUsageRepository(),
    )

    result = service.get_plan_and_usage(db_session=None, tenant_id=uuid4())
    assert result == {"plan": None, "status": None, "usage": expected_usage}


def test_get_plan_and_usage_returns_plan_and_status_when_account_exists():
    expected_tenant_id = uuid4()

    class FakeBillingAccount:
        plan = "pro"
        status = "active"

    class FakeBillingRepository:
        def get_billing_account(self, db_session, tenant_id):
            assert tenant_id == expected_tenant_id
            return FakeBillingAccount()

    class FakeUsageRepository:
        def get_current_usage(self, db_session, tenant_id):
            return {"reports_this_month": 5}

    service = BillingService(
        billing_repository=FakeBillingRepository(),
        usage_repository=FakeUsageRepository(),
    )

    result = service.get_plan_and_usage(db_session=None, tenant_id=expected_tenant_id)
    assert result["plan"] == "pro"
    assert result["status"] == "active"
    assert result["usage"]["reports_this_month"] == 5


def test_create_checkout_session_raises_400_when_target_plan_empty():
    service = BillingService()
    with pytest.raises(HTTPException) as exc_info:
        service.create_checkout_session(
            db_session=None, tenant_id=uuid4(), target_plan=""
        )
    assert exc_info.value.status_code == 400


def test_create_checkout_session_calls_stripe_client():
    expected_tenant_id = uuid4()

    class FakeStripeClient:
        def create_checkout_session(self, tenant_id: str, target_plan: str):
            assert tenant_id == str(expected_tenant_id)
            assert target_plan == "starter"
            return {"checkout_session_id": "cs_test"}

    service = BillingService(stripe_client=FakeStripeClient())
    result = service.create_checkout_session(
        db_session=None, tenant_id=expected_tenant_id, target_plan="starter"
    )
    assert result["checkout_session_id"] == "cs_test"
