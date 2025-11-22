"""Local stub Stripe client.

TODO: Replace with real Stripe SDK integration.
"""

from typing import Any


class StripeClient:
    def create_checkout_session(
        self, tenant_id: str, target_plan: str
    ) -> dict[str, Any]:
        return {
            "checkout_session_id": "cs_test_123",
            "url": "https://checkout.stripe.local/session/cs_test_123",
            "tenant_id": tenant_id,
            "target_plan": target_plan,
        }
