"""Pydantic schemas for drive endpoints."""

import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import Field, model_validator

from app.models.enums import ConversionType, DriveType, OAMode, ProcessMode
from app.schemas.common import BaseSchema, TimestampMixin


# ── Eligibility ───────────────────────────────────────────────────────────────

class EligibilityStatus(str, Enum):
    """Three-way eligibility result for a student viewing a drive."""
    ELIGIBLE = "ELIGIBLE"
    NOT_ELIGIBLE = "NOT_ELIGIBLE"
    NOT_RELEVANT = "NOT_RELEVANT"  # Wrong graduation batch


class EligibilityResponse(BaseSchema):
    """Structured eligibility result returned to the frontend."""

    status: EligibilityStatus
    eligible: bool
    reasons: list[str] = Field(default_factory=list)


# ── Drive Request Schemas ─────────────────────────────────────────────────────

class DriveCreateRequest(BaseSchema):
    """Request body for SPC to create a new placement drive."""

    company_id: uuid.UUID
    title: str = Field(min_length=1, max_length=500)
    drive_type: DriveType
    conversion_type: ConversionType | None = None
    target_graduation_year: int = Field(ge=2020, le=2035)
    eligible_branches: list[str] = Field(
        min_length=1, description="At least one branch must be specified."
    )
    stipend: Decimal | None = Field(default=None, ge=0)
    ctc: Decimal | None = Field(default=None, ge=0)
    location: str | None = Field(default=None, max_length=500)
    ppt_datetime: datetime | None = None
    oa_datetime: datetime | None = None
    oa_deadline: datetime
    oa_mode: OAMode | None = None
    process_mode: ProcessMode | None = None
    minimum_cgpa: Decimal | None = Field(default=None, ge=0, le=10)
    maximum_backlogs: int = Field(default=0, ge=0)
    type_placement_policy: str | None = Field(default=None, max_length=500)
    job_description_url: str | None = Field(default=None, max_length=2048)
    additional_announcements: str | None = None

    @model_validator(mode="after")
    def validate_branches_not_empty(self) -> "DriveCreateRequest":
        if not self.eligible_branches:
            raise ValueError("eligible_branches must contain at least one branch.")
        # Normalize branches to uppercase
        self.eligible_branches = [b.strip().upper() for b in self.eligible_branches]
        return self


class DriveUpdateRequest(BaseSchema):
    """Request body for SPC to partially update a drive (unpublished only)."""

    title: str | None = Field(default=None, min_length=1, max_length=500)
    drive_type: DriveType | None = None
    conversion_type: ConversionType | None = None
    target_graduation_year: int | None = Field(default=None, ge=2020, le=2035)
    eligible_branches: list[str] | None = None
    stipend: Decimal | None = Field(default=None, ge=0)
    ctc: Decimal | None = Field(default=None, ge=0)
    location: str | None = Field(default=None, max_length=500)
    ppt_datetime: datetime | None = None
    oa_datetime: datetime | None = None
    oa_deadline: datetime | None = None
    oa_mode: OAMode | None = None
    process_mode: ProcessMode | None = None
    minimum_cgpa: Decimal | None = Field(default=None, ge=0, le=10)
    maximum_backlogs: int | None = Field(default=None, ge=0)
    type_placement_policy: str | None = Field(default=None, max_length=500)
    job_description_url: str | None = Field(default=None, max_length=2048)
    additional_announcements: str | None = None


# ── Drive Response Schemas ────────────────────────────────────────────────────

class DriveResponse(TimestampMixin):
    """Full drive detail returned to students and SPC."""

    id: uuid.UUID
    company_id: uuid.UUID
    company_name: str  # Joined from companies table
    title: str
    drive_type: DriveType
    conversion_type: ConversionType | None
    target_graduation_year: int
    stipend: Decimal | None
    ctc: Decimal | None
    location: str | None
    ppt_datetime: datetime | None
    oa_datetime: datetime | None
    oa_deadline: datetime
    oa_mode: OAMode | None
    process_mode: ProcessMode | None
    eligible_branches: list[str]  # Extracted from DriveEligibleBranch rows
    minimum_cgpa: Decimal | None
    maximum_backlogs: int
    type_placement_policy: str | None = None
    job_description_url: str | None
    additional_announcements: str | None
    published: bool
    published_at: datetime | None
    created_by: uuid.UUID | None
    # Contextual fields injected by the service layer (not from DB columns directly)
    eligibility: EligibilityResponse | None = None
    application_status: str | None = None  # current student's application status if applied


    applicant_count: int | None = Field(
        default=None,
        description="Number of applicants. Only populated after the "
        "application deadline has passed.",
    )


class DriveListItem(BaseSchema):
    """Compact drive item for list endpoints."""

    id: uuid.UUID
    company_id: uuid.UUID
    company_name: str
    type_placement_policy: str | None = None
    title: str
    drive_type: DriveType
    conversion_type: ConversionType | None
    target_graduation_year: int
    stipend: Decimal | None
    ctc: Decimal | None
    location: str | None
    ppt_datetime: datetime | None = None
    oa_datetime: datetime | None = None
    oa_deadline: datetime
    published_at: datetime | None
    eligible_branches: list[str]
    job_description_url: str | None = None
    additional_announcements: str | None = None
    eligibility: EligibilityResponse | None = None
    application_status: str | None = None


class DriveListResponse(BaseSchema):
    """Paginated drive list."""

    total: int
    page: int
    page_size: int
    items: list[DriveListItem]


class PublishDriveResponse(BaseSchema):
    """Response after publishing a drive."""

    message: str
    drive_id: uuid.UUID
    published_at: datetime


# ── Drive Filter Params ───────────────────────────────────────────────────────

class DriveFeedFilter(BaseSchema):
    """Query parameters for the drive feed endpoint (validated via Pydantic)."""

    for_me: bool = Field(
        default=False,
        description="If true, filter by the student's graduation year.",
    )
    search: str | None = Field(default=None, description="Search company name or drive title.")
    drive_type: DriveType | None = None
    conversion_type: ConversionType | None = None
    location: str | None = None
    min_ctc: Decimal | None = Field(default=None, ge=0)
    max_ctc: Decimal | None = Field(default=None, ge=0)
    oa_from: datetime | None = None
    oa_to: datetime | None = None
    published_from: datetime | None = None
    target_graduation_year: int | None = Field(default=None, ge=2020, le=2035)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
