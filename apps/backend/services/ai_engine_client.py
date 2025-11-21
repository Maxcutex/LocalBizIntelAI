"""Local stub client for AI-engine interactions.

This will be replaced by a real HTTP client when the AI service is deployed.
"""

from typing import Any


class AiEngineClient:
    """Client for generating AI-powered insights."""

    def generate_market_summary(self, payload: dict[str, Any]) -> dict[str, Any]:
        city = payload.get("city", "unknown city")
        return {
            "summary": f"Market summary for {city}.",
        }

    def generate_opportunity_commentary(
        self, ranked_regions: list[dict[str, Any]]
    ) -> dict[str, Any]:
        return {
            "commentary": "Opportunities generated.",
            "regions": ranked_regions,
        }
