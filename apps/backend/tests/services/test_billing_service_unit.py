"""Unit tests for `BillingService` business logic."""

from uuid import uuid4

import pytest
from fastapi import HTTPException

from services.billing_service import BillingService
from services.dependencies import BillingServiceDependencies


def test_get_plan_and_usage_returns_none_plan_when_no_account():
    """No billing account yields null plan/status with usage populated."""
    expected_usage = {"reports_this_month": 2}

    class FakeBillingRepository:
        """Fake billing repository returning no account."""

        def get_billing_account(self, _db_session, _tenant_id):
            """Return no billing account."""
            return None

    class FakeUsageRepository:
        """Fake usage repository returning expected usage."""

        def get_current_usage(self, _db_session, tenant_id):
            """Return canned usage."""
            assert tenant_id is not None
            return expected_usage

    class DummyStripeClient:
        """Stub stripe client."""

        def create_checkout_session(self, _tenant_id: str, _target_plan: str):
            """Return empty session payload."""
            return {}

    service = BillingService(
        BillingServiceDependencies(
            billing_repository=FakeBillingRepository(),
            usage_repository=FakeUsageRepository(),
            stripe_client=DummyStripeClient(),
        )
    )

    result = service.get_plan_and_usage(db_session=None, tenant_id=uuid4())
    assert result == {"plan": None, "status": None, "usage": expected_usage}


def test_get_plan_and_usage_returns_plan_and_status_when_account_exists():
    """Existing billing account yields its plan/status with usage."""
    expected_tenant_id = uuid4()

    class FakeBillingAccount:
        """Minimal billing account fixture."""

        plan = "pro"
        status = "active"

    class FakeBillingRepository:
        """Fake billing repository returning an account."""

        def get_billing_account(self, _db_session, tenant_id):
            """Return a canned billing account."""
            assert tenant_id == expected_tenant_id
            return FakeBillingAccount()

    class FakeUsageRepository:
        """Fake usage repository."""

        def get_current_usage(self, _db_session, _tenant_id):
            """Return canned usage."""
            return {"reports_this_month": 5}

    class DummyStripeClient:
        """Stub stripe client."""

        def create_checkout_session(self, _tenant_id: str, _target_plan: str):
            """Return empty session payload."""
            return {}

    service = BillingService(
        BillingServiceDependencies(
            billing_repository=FakeBillingRepository(),
            usage_repository=FakeUsageRepository(),
            stripe_client=DummyStripeClient(),
        )
    )

    result = service.get_plan_and_usage(db_session=None, tenant_id=expected_tenant_id)
    assert result["plan"] == "pro"
    assert result["status"] == "active"
    assert result["usage"]["reports_this_month"] == 5


def test_create_checkout_session_raises_400_when_target_plan_empty():
    """Empty target plan raises 400."""

    class DummyBillingRepository:
        """Stub billing repository."""

        def get_billing_account(self, _db_session, _tenant_id):
            """Return no billing account."""
            return None

    class DummyUsageRepository:
        """Stub usage repository."""

        def get_current_usage(self, _db_session, _tenant_id):
            """Return empty usage."""
            return {}

    class DummyStripeClient:
        """Stub stripe client."""

        def create_checkout_session(self, _tenant_id: str, _target_plan: str):
            """Return empty session payload."""
            return {}

    service = BillingService(
        BillingServiceDependencies(
            billing_repository=DummyBillingRepository(),
            usage_repository=DummyUsageRepository(),
            stripe_client=DummyStripeClient(),
        )
    )
    with pytest.raises(HTTPException) as exc_info:
        service.create_checkout_session(
            db_session=None, tenant_id=uuid4(), target_plan=""
        )
    assert exc_info.value.status_code == 400


def test_create_checkout_session_calls_stripe_client():
    """Stripe client is invoked with tenant id and target plan."""
    expected_tenant_id = uuid4()

    class FakeStripeClient:
        """Fake stripe client asserting on input."""

        def create_checkout_session(self, tenant_id: str, target_plan: str):
            """Return checkout session payload."""
            assert tenant_id == str(expected_tenant_id)
            assert target_plan == "starter"
            return {"checkout_session_id": "cs_test"}

    class DummyBillingRepository:
        """Stub billing repository."""

        def get_billing_account(self, _db_session, _tenant_id):
            """Return no billing account."""
            return None

    class DummyUsageRepository:
        """Stub usage repository."""

        def get_current_usage(self, _db_session, _tenant_id):
            """Return empty usage."""
            return {}

    service = BillingService(
        BillingServiceDependencies(
            billing_repository=DummyBillingRepository(),
            usage_repository=DummyUsageRepository(),
            stripe_client=FakeStripeClient(),
        )
    )
    result = service.create_checkout_session(
        db_session=None, tenant_id=expected_tenant_id, target_plan="starter"
    )
    assert result["checkout_session_id"] == "cs_test"
