"""Pydantic schemas for student endpoints."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import Field, field_validator

from app.schemas.common import BaseSchema, TimestampMixin


class StudentResponse(TimestampMixin):
    """Full student profile returned to the student themselves or SPC/Admin."""

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    usn: str
    branch: str
    date_of_birth: date | None
    graduation_year: int
    tenth_percentage: Decimal | None
    twelfth_percentage: Decimal | None
    cgpa: Decimal | None
    backlogs: int
    resume_url: str | None
    profile_frozen: bool
    cgpa_unlocked_until: datetime | None
    backlogs_unlocked_until: datetime | None


# app/schemas/student.py
# REPLACE StudentUpdateRequest — usn and graduation_year still missing

class StudentUpdateRequest(BaseSchema):
    resume_url: str | None = Field(default=None, max_length=2048)
    cgpa: Decimal | None = Field(default=None, ge=0, le=10)
    backlogs: int | None = Field(default=None, ge=0)
    name: str | None = Field(default=None, min_length=1, max_length=200)
    usn: str | None = Field(default=None, min_length=1, max_length=20)
    branch: str | None = Field(default=None, min_length=1, max_length=100)
    graduation_year: int | None = Field(default=None, ge=2000, le=2100)
    date_of_birth: date | None = None
    tenth_percentage: Decimal | None = Field(default=None, ge=0, le=100)
    twelfth_percentage: Decimal | None = Field(default=None, ge=0, le=100)


# app/schemas/student.py
# REPLACE StudentUpdateRequest with this — adds usn and graduation_year

# app/schemas/student.py
# REPLACE StudentResponse — make pre-profile-setup-nullable fields Optional

class StudentResponse(BaseSchema):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str | None = None
    usn: str | None = None
    branch: str | None = None
    date_of_birth: date | None = None
    graduation_year: int | None = None
    tenth_percentage: Decimal | None = None
    twelfth_percentage: Decimal | None = None
    cgpa: Decimal | None = None
    backlogs: int
    resume_url: str | None = None
    profile_frozen: bool
    cgpa_unlocked_until: datetime | None = None
    backlogs_unlocked_until: datetime | None = None
    created_at: datetime
    updated_at: datetime

class UnlockFieldRequest(BaseSchema):
    """SPC request to temporarily unlock CGPA or backlogs for a student."""

    unlock_hours: int = Field(default=24, ge=1, le=720, description="Hours to unlock the field")


class StudentListResponse(BaseSchema):
    """Paginated student list for SPC."""

    total: int
    page: int
    page_size: int
    items: list[StudentResponse]
