"""AI-engine client for generating LLM-backed insights.

In local/dev:
- If `OPENAI_API_KEY` is set, calls OpenAI Chat Completions.
- If not set (or OpenAI is not installed), falls back to simple stub outputs.

This keeps the interface stable while allowing a real vertical slice to ship.
"""

import json
from typing import Any

from api.config import Settings

try:
    from openai import OpenAI as OPENAI_CLIENT_CLASS  # type: ignore[import-untyped]
except ModuleNotFoundError:  # pragma: no cover
    OPENAI_CLIENT_CLASS = None  # type: ignore[assignment,misc]


class AiEngineClient:
    """Client for generating AI-powered insights via an LLM."""

    def __init__(
        self,
        settings: Settings,
        api_key: str | None = None,
        model: str | None = None,
        timeout_s: float | None = None,
        openai_client: Any | None = None,
    ) -> None:
        self._settings = settings
        self._api_key = api_key or settings.openai_api_key
        self._model: str = model or settings.openai_model
        self._timeout_s = timeout_s or settings.openai_timeout_s

        if openai_client is not None:
            self._openai_client = openai_client
        else:
            self._openai_client = None
            if self._api_key and OPENAI_CLIENT_CLASS is not None:
                self._openai_client = OPENAI_CLIENT_CLASS(
                    api_key=self._api_key,
                    timeout=self._timeout_s,
                    max_retries=1,
                )

    def _call_llm_json(
        self,
        system_prompt: str,
        user_payload: dict[str, Any],
    ) -> dict[str, Any]:
        if self._openai_client is None:
            raise RuntimeError("OpenAI client not configured")

        response = self._openai_client.chat.completions.create(
            # type: ignore[call-overload]
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": json.dumps(user_payload, default=str),
                },
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content or "{}"
        parsed = json.loads(content)
        if not isinstance(parsed, dict):
            return {}

        sanitized = self._strip_numeric_values(parsed)
        return sanitized

    @staticmethod
    def _strip_numeric_values(value: Any) -> Any:
        """
        Ensure LLM outputs do not introduce new numeric facts.

        We allow numbers only from our DB outputs. Since the LLM response
        is constrained to narrative JSON (strings + lists), any numeric leaf
        value is removed to avoid hallucinated stats.
        """

        if isinstance(value, dict):
            return {
                key: AiEngineClient._strip_numeric_values(item)
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [AiEngineClient._strip_numeric_values(item) for item in value]
        if isinstance(value, (int, float)):
            return None
        return value

    def generate_market_summary(self, payload: dict[str, Any]) -> dict[str, Any]:
        if self._openai_client is None:
            city = payload.get("city", "unknown city")
            return {"summary": f"Market summary for {city}."}

        system_prompt = (
            "You are an analyst generating a concise market summary. "
            'Return JSON like {"summary": "...", "highlights": ["..."], '
            '"risks": ["..."]}. Use the provided stats only.'
        )
        try:
            return self._call_llm_json(system_prompt, payload)
        except Exception:
            city = payload.get("city", "unknown city")
            return {"summary": f"Market summary for {city} is unavailable currently."}

    def generate_opportunity_commentary(
        self, ranked_regions: list[dict[str, Any]]
    ) -> dict[str, Any]:
        if self._openai_client is None:
            return {
                "commentary": "Opportunities generated.",
                "region_rationales": [
                    {
                        "geo_id": region.get("geo_id"),
                        "rationale": "Ranked based on composite opportunity score.",
                    }
                    for region in ranked_regions
                ],
            }

        system_prompt = (
            "You are an expert market strategist. Given ranked regions with demand, "
            "supply, competition, and composite scores, write a short commentary "
            "explaining why the top regions are attractive/weak. "
            'Return JSON like {"commentary": "...", '
            '"region_rationales": [{"geo_id": "...", "rationale": "..."}]}. '
            "Be factual and grounded in the scores. Keep it brief."
        )
        try:
            result = self._call_llm_json(
                system_prompt,
                {"ranked_regions": ranked_regions},
            )
            if "commentary" not in result:
                result["commentary"] = "AI commentary generated."
            return result
        except Exception:
            return {
                "commentary": "AI commentary unavailable at the moment.",
                "region_rationales": [
                    {
                        "geo_id": region.get("geo_id"),
                        "rationale": "Ranked based on composite opportunity score.",
                    }
                    for region in ranked_regions
                ],
            }

    def generate_personas(self, input_payload: dict[str, Any]) -> dict[str, Any]:
        if self._openai_client is None:
            city = input_payload.get("city", "unknown city")
            business_type = input_payload.get("business_type")
            headline = f"Personas for {city}"
            if business_type:
                headline = f"Personas for {city} ({business_type})"
            return {"headline": headline, "personas": []}

        system_prompt = (
            "You generate customer personas for a business. "
            'Return JSON like {"headline": "...", "personas": '
            '[{"name": "...", "description": "..."}]}. '
            "Use the provided stats only."
        )
        try:
            return self._call_llm_json(system_prompt, input_payload)
        except Exception:
            city = input_payload.get("city", "unknown city")
            return {
                "headline": f"Personas for {city} unavailable currently.",
                "personas": [],
            }
