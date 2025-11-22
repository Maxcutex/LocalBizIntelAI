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

from api.config import get_settings
from api.security.jwt import try_verify_access_token
from models.db import SessionLocal


class CurrentRequestContext(BaseModel):
    """
    Request-scoped auth context.

    Supports bearer JWT auth. In local/dev, falls back to header-based auth.
    """

    user_id: UUID
    tenant_id: UUID
    role: str = "USER"


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
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
) -> CurrentRequestContext:
    """
    Auth context dependency.

    Preferred: `Authorization: Bearer <access_token>`.

    Local/dev fallback: `X-User-Id` and `X-Tenant-Id` headers.
    """

    settings = get_settings()

    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        payload = try_verify_access_token(token=token, settings=settings)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired access token",
            )
        try:
            return CurrentRequestContext(
                user_id=UUID(payload["sub"]),
                tenant_id=UUID(payload["tenant_id"]),
                role=str(payload.get("role") or "USER"),
            )
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid access token claims",
            ) from exc

    if settings.debug or settings.environment == "local":
        if x_user_id is None or x_tenant_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authentication headers",
            )
        try:
            return CurrentRequestContext(
                user_id=UUID(x_user_id),
                tenant_id=UUID(x_tenant_id),
                role="USER",
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid authentication header format",
            ) from exc

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing Authorization header",
    )


def require_admin(
    context: CurrentRequestContext = Header(None, include_in_schema=False),
) -> CurrentRequestContext:
    """Guard that requires ADMIN role."""

    if context.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )
    return context
