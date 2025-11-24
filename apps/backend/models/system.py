"""System metadata and ETL ORM models."""

import uuid

from sqlalchemy import JSON, String
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class DataFreshness(Base):
    """Dataset freshness ORM model for monitoring ETL recency."""

    __tablename__ = "data_freshness"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    dataset_name: Mapped[str] = mapped_column(String, nullable=False)
    last_run: Mapped[str | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    row_count: Mapped[int | None] = mapped_column(nullable=True)
    status: Mapped[str | None] = mapped_column(String, nullable=True)


class ETLLog(Base):
    """ETL log ORM model capturing run payloads and outcomes."""

    __tablename__ = "etl_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_name: Mapped[str] = mapped_column(String, nullable=False)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[str | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
