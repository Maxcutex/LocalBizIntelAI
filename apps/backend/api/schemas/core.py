"""Core Pydantic schemas for tenants and users."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr
from pydantic.config import ConfigDict


class TenantBase(BaseModel):
    name: str
    plan: str


class TenantCreate(TenantBase):
    pass


class TenantRead(TenantBase):
    id: UUID
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class UserBase(BaseModel):
    email: EmailStr
    name: str
    role: str


class UserCreate(UserBase):
    tenant_id: UUID


class UserRead(UserBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


