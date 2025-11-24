"""Pydantic schemas for auth endpoints."""

from uuid import UUID

from pydantic import BaseModel, Field


class DevLoginRequest(BaseModel):
    """Development-only login payload for issuing a JWT."""

    user_id: UUID
    tenant_id: UUID
    role: str = Field(default="USER", min_length=1)


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"
