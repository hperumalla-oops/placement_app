"""Application routes.

The core student-facing action: POST /drives/{drive_id}/apply. All
eligibility, deadline, and duplicate checks are re-verified server-side in
ApplicationService — see spec section 16.
"""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_student, get_current_user, require_spc
from app.core.database import get_db
from app.models.application import Application
from app.models.student import Student
from app.models.user import User
from app.schemas.application import (
    ApplicationCreateResponse,
    ApplicationResponse,
    DriveApplicationListResponse,
    StudentApplicationListResponse,
)
from app.services.application_service import ApplicationService

router = APIRouter(tags=["Applications"])


def _to_response(application: Application) -> ApplicationResponse:
    drive = getattr(application, "drive", None)
    return ApplicationResponse(
        id=application.id,
        student_id=application.student_id,
        drive_id=application.drive_id,
        status=application.status,
        applied_at=application.applied_at,
        updated_at=application.updated_at,
        drive_title=drive.title if drive else None,
        company_name=drive.company.name if drive and drive.company else None,
    )


@router.post(
    "/drives/{drive_id}/apply",
    response_model=ApplicationCreateResponse,
    status_code=201,
    summary="Apply to a drive (students only)",
)
async def apply_to_drive(
    drive_id: uuid.UUID,
    student: Student = Depends(get_current_student),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApplicationCreateResponse:
    service = ApplicationService(db)
    application = await service.apply_to_drive(student, drive_id, current_user)
    return ApplicationCreateResponse(
        message="Application submitted successfully.",
        application=_to_response(application),
    )


@router.get(
    "/applications/me",
    response_model=StudentApplicationListResponse,
    summary="List the authenticated student's applications",
)
async def get_my_applications(
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
) -> StudentApplicationListResponse:
    service = ApplicationService(db)
    applications = await service.get_student_applications(student)
    return StudentApplicationListResponse(
        total=len(applications),
        items=[_to_response(a) for a in applications],
    )


@router.get(
    "/drives/{drive_id}/applications",
    response_model=DriveApplicationListResponse,
    summary="List applications for a drive (SPC/Admin only)",
    dependencies=[Depends(require_spc)],
)
async def get_drive_applications(
    drive_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> DriveApplicationListResponse:
    service = ApplicationService(db)
    applications, total = await service.get_drive_applications(
        drive_id, page=page, page_size=page_size
    )
    return DriveApplicationListResponse(
        drive_id=drive_id,
        total=total,
        items=[_to_response(a) for a in applications],
    )