"""Local stub client for AI-engine interactions.

This will be replaced by a real HTTP client when the AI service is deployed.
"""

from typing import Any


class AiEngineClient:
    """Client for generating AI-powered insights.

    TODO: Replace these stub methods with real AI-engine HTTP calls and
    structured outputs once the AI service is deployed.
    """

    def generate_market_summary(self, payload: dict[str, Any]) -> dict[str, Any]:
        # TODO: Call AI engine to generate a narrative summary from payload.
        city = payload.get("city", "unknown city")
        return {
            "summary": f"Market summary for {city}.",
        }

    def generate_opportunity_commentary(
        self, ranked_regions: list[dict[str, Any]]
    ) -> dict[str, Any]:
        # TODO: Call AI engine to generate commentary for ranked regions.
        return {
            "commentary": "Opportunities generated.",
            "regions": ranked_regions,
        }

    def generate_personas(self, input_payload: dict[str, Any]) -> dict[str, Any]:
        # TODO: Call AI engine to generate personas from input payload.
        city = input_payload.get("city", "unknown city")
        business_type = input_payload.get("business_type")
        headline = f"Personas for {city}"
        if business_type:
            headline = f"Personas for {city} ({business_type})"
        return {
            "headline": headline,
            "personas": [],
        }
