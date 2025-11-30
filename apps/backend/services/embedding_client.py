"""Embedding client for generating vector embeddings.

Uses OpenAI embeddings when configured; otherwise falls back to deterministic
local embeddings (useful for tests and local/dev without API keys).
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any

from api.config import Settings

try:
    from openai import OpenAI as OPENAI_CLIENT_CLASS  # type: ignore[import-untyped]
except ModuleNotFoundError:  # pragma: no cover
    OPENAI_CLIENT_CLASS = None  # type: ignore[assignment,misc]

logger = logging.getLogger(__name__)


class EmbeddingClient:
    def __init__(
        self,
        *,
        settings: Settings,
        api_key: str | None = None,
        model: str | None = None,
        dimensions: int | None = None,
        timeout_s: float | None = None,
        openai_client: Any | None = None,
    ) -> None:
        self._settings = settings
        self._api_key = api_key or settings.openai_api_key
        self._model = model or settings.openai_embedding_model
        self._dimensions = dimensions or settings.openai_embedding_dimensions
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

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        if self._openai_client is None:
            logger.info(
                "OpenAI client not configured; using deterministic stub embeddings",
                extra={"text_count": len(texts), "dimensions": self._dimensions},
            )
            return [self._stub_embedding(text) for text in texts]

        logger.info(
            "Generating embeddings",
            extra={
                "model": self._model,
                "text_count": len(texts),
                "dimensions": self._dimensions,
            },
        )
        response = self._openai_client.embeddings.create(  # type: ignore[call-overload]
            model=self._model,
            input=texts,
            dimensions=self._dimensions,
        )
        return [item.embedding for item in response.data]

    def _stub_embedding(self, text: str) -> list[float]:
        """
        Deterministic embedding of fixed dimension.

        This is not semantically meaningful; it's purely for stable tests/dev.
        """
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        values: list[float] = []
        for idx in range(self._dimensions):
            b = digest[idx % len(digest)]
            # Map 0..255 to -1..1
            values.append((b / 127.5) - 1.0)
        return values
