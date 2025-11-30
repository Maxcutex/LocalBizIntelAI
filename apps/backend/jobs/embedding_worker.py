"""Embedding worker stub.

Consumes a Pub/Sub-style JSON payload and dispatches to embedding jobs.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Protocol

from sqlalchemy.orm import Session

from jobs.rebuild_embeddings_job import RebuildEmbeddingsJob

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingMessage:
    job_name: str
    country: str | None
    city: str | None
    regions: list[str] | None
    options: dict[str, Any]

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "EmbeddingMessage":
        job_name = str(payload.get("job_name") or "")
        regions = payload.get("regions")
        resolved_regions: list[str] | None = None
        if isinstance(regions, list) and all(isinstance(x, str) for x in regions):
            resolved_regions = list(regions)
        return cls(
            job_name=job_name,
            country=payload.get("country"),
            city=payload.get("city"),
            regions=resolved_regions,
            options=payload.get("options") or {},
        )


class EmbeddingHandler(Protocol):
    def run(
        self,
        *,
        db_session: Session,
        country: str | None,
        city: str | None,
        regions: list[str] | None,
        options: dict[str, Any],
    ) -> Any:
        raise NotImplementedError


class EmbeddingWorker:
    def __init__(self, *, handlers_by_job_name: dict[str, EmbeddingHandler]) -> None:
        self._handlers_by_job_name = {
            self._normalize_job_name(name): handler
            for name, handler in handlers_by_job_name.items()
        }

    @classmethod
    def create_default(cls) -> "EmbeddingWorker":
        rebuild_job = RebuildEmbeddingsJob.create_default()
        return cls(handlers_by_job_name={"rebuild-embeddings": rebuild_job})

    def consume(
        self, *, db_session: Session, payload: dict[str, Any]
    ) -> dict[str, Any]:
        message = EmbeddingMessage.from_payload(payload)
        normalized_job = self._normalize_job_name(message.job_name)
        handler = self._handlers_by_job_name.get(normalized_job)
        if not handler:
            logger.error(
                "Unsupported embedding job",
                extra={"job_name": message.job_name},
            )
            raise ValueError(f"Unsupported embedding job: {message.job_name}")

        logger.info(
            "Consuming embedding message",
            extra={
                "job_name": normalized_job,
                "country": message.country,
                "city": message.city,
                "region_count": len(message.regions) if message.regions else None,
            },
        )
        result = handler.run(
            db_session=db_session,
            country=message.country,
            city=message.city,
            regions=message.regions,
            options=message.options,
        )
        output = result.__dict__
        logger.info(
            "Embedding message processed",
            extra={
                "job_name": normalized_job,
                "status": output.get("status"),
                "row_count": output.get("row_count"),
            },
        )
        return output

    @staticmethod
    def _normalize_job_name(job_name: str) -> str:
        return job_name.lower().strip()
