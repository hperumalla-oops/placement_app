"""Pydantic schemas for authentication endpoints."""

import uuid
from datetime import datetime

from app.models.enums import UserRole
from app.schemas.common import BaseSchema, TimestampMixin



class UserResponse( TimestampMixin):
    """Authenticated user information returned by /auth/me."""

    id: uuid.UUID
    email: str
    role: UserRole
