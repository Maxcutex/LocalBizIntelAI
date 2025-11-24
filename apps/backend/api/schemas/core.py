"""Core Pydantic schemas for tenants and users."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr
from pydantic.config import ConfigDict


class TenantBase(BaseModel):
    """Shared tenant fields."""

    name: str
    plan: str


class TenantCreate(TenantBase):
    """Payload for creating a tenant."""


class TenantRead(TenantBase):
    """Tenant response schema."""

    id: UUID
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class UserBase(BaseModel):
    """Shared user fields."""

    email: EmailStr
    name: str
    role: str


class UserCreate(UserBase):
    """Payload for creating a user."""

    tenant_id: UUID


class UserRead(UserBase):
    """User response schema."""

    id: UUID
    tenant_id: UUID
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
