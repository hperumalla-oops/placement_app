# """Pydantic schemas for application endpoints."""

import uuid
from datetime import datetime

from app.models.enums import ApplicationStatus
from app.schemas.common import BaseSchema


class ApplicationResponse(BaseSchema):
    """Single application detail."""

    id: uuid.UUID
    student_id: uuid.UUID
    drive_id: uuid.UUID
    status: ApplicationStatus
    applied_at: datetime
    updated_at: datetime
    # Injected: drive summary info for student's application list
    drive_title: str | None = None
    company_name: str | None = None



from pydantic import BaseModel, Field

class ApplicationCreateRequest(BaseModel):
    drive_id: uuid.UUID
    confirmed_details_accurate: bool = Field(
        ...,
        description="Student explicitly confirms profile details are accurate "
        "and they understand the consequences of applying.",
    )




class ApplicationCreateResponse(BaseSchema):
    """Response after a student successfully applies to a drive."""

    message: str
    application: ApplicationResponse


class StudentApplicationListResponse(BaseSchema):
    """All applications for the authenticated student."""

    total: int
    items: list[ApplicationResponse]


class DriveApplicationListResponse(BaseSchema):
    """All applications for a specific drive (SPC view)."""

    drive_id: uuid.UUID
    total: int
    items: list[ApplicationResponse]


# class ApplicationStatusUpdateRequest(BaseSchema):
#     """SPC request to update an application's status."""

#     status: ApplicationStatus


# app/schemas/application.py
# ADD this schema (create the file if it doesn't already exist)

