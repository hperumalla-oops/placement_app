"""Shared Pydantic schema utilities and base classes."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Base schema with ORM mode enabled for all response schemas."""

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseSchema):
    """Generic success/informational message response."""

    message: str


class PaginatedResponse(BaseSchema):
    """Wrapper for paginated list endpoints."""

    total: int
    page: int
    page_size: int
    items: list  # subclasses should override with typed list


class TimestampMixin(BaseSchema):
    """Adds created_at and updated_at to any response schema."""

    created_at: datetime
    updated_at: datetime
