"""Worker endpoints for Pub/Sub push subscriptions.

These endpoints are intended to be deployed as a separate Cloud Run service
("data-ingestion-worker" / "embedding-worker"), but live in the same codebase.
"""

from __future__ import annotations

import base64
import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.dependencies import get_db
from jobs.embedding_worker import EmbeddingWorker
from jobs.ingestion_worker import IngestionWorker

logger = logging.getLogger(__name__)
router = APIRouter()


class PubSubPushMessage(BaseModel):
    data: str = Field(min_length=1)
    attributes: dict[str, str] | None = None


class PubSubPushEnvelope(BaseModel):
    message: PubSubPushMessage
    subscription: str | None = None


def _decode_pubsub_data(data_b64: str) -> dict[str, Any]:
    try:
        decoded = base64.b64decode(data_b64).decode("utf-8")
        parsed = json.loads(decoded)
        if not isinstance(parsed, dict):
            raise ValueError("Pub/Sub payload must be a JSON object")
        return parsed
    except Exception as exc:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Invalid Pub/Sub message payload",
        ) from exc


@router.post("/ingestion", summary="Consume ingestion job (Pub/Sub push)")
def consume_ingestion_job(
    envelope: PubSubPushEnvelope,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    payload = _decode_pubsub_data(envelope.message.data)
    worker = IngestionWorker.create_default()
    result = worker.consume(db_session=db, payload=payload)
    return {"status": "OK", "result": result}


@router.post("/embeddings", summary="Consume embedding job (Pub/Sub push)")
def consume_embedding_job(
    envelope: PubSubPushEnvelope,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    payload = _decode_pubsub_data(envelope.message.data)
    worker = EmbeddingWorker.create_default()
    result = worker.consume(db_session=db, payload=payload)
    return {"status": "OK", "result": result}
