"""
Shared FastAPI dependency functions.

Use this module to define common dependency-injected objects,
such as database sessions, current user, settings, etc.
"""

from collections.abc import Generator
from uuid import UUID

from fastapi import Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from models.db import SessionLocal


class CurrentRequestContext(BaseModel):
    """
    Request-scoped auth context.

    For now this is hydrated from headers to keep the backend runnable
    before JWT integration is wired. Replace with real JWT parsing later.
    """

    user_id: UUID
    tenant_id: UUID


def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency.

    Yields a SQLAlchemy session that is closed after the request ends.
    Use in route signatures as:

        def endpoint(db: Session = Depends(get_db)):
            ...
    """

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_request_context(
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
) -> CurrentRequestContext:
    """
    Temporary auth context dependency.

    Clients must pass `X-User-Id` and `X-Tenant-Id` headers.
    """

    if x_user_id is None or x_tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication headers",
        )
    try:
        return CurrentRequestContext(
            user_id=UUID(x_user_id),
            tenant_id=UUID(x_tenant_id),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid authentication header format",
        ) from exc
