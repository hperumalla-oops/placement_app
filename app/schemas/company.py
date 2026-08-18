"""Pydantic schemas for company endpoints."""

import uuid
from datetime import datetime

from pydantic import Field

from app.schemas.common import BaseSchema, TimestampMixin


class CompanyCreate(BaseSchema):
    """Request body for creating a new company."""

    name: str = Field(min_length=1, max_length=500)


class CompanyUpdate(BaseSchema):
    """Request body for updating an existing company."""

    name: str | None = Field(default=None, min_length=1, max_length=500)


class CompanyResponse(TimestampMixin):
    """Company detail response."""

    id: uuid.UUID
    name: str


class CompanyListResponse(BaseSchema):
    """Paginated list of companies."""

    total: int
    items: list[CompanyResponse]
