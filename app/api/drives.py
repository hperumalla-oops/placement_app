"""Drive routes.

Students can read published drives (with per-student eligibility computed
server-side). SPC/Admin can create, update, and publish drives.

Per spec section 14, drives are visible to all students regardless of
whether they are eligible — the response distinguishes ELIGIBLE /
NOT_ELIGIBLE / NOT_RELEVANT rather than hiding rows.
"""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_spc
from app.core.database import get_db
from app.models.drive import Drive
from app.models.enums import ConversionType, DriveType
from app.models.student import Student
from app.models.user import User, UserRole
from app.repositories.application import ApplicationRepository
from app.schemas.drive import (
    DriveCreateRequest,
    DriveFeedFilter,
    DriveListItem,
    DriveListResponse,
    DriveResponse,
    DriveUpdateRequest,
    EligibilityResponse,
    EligibilityStatus,
    PublishDriveResponse,
)
from app.repositories.student import StudentRepository
from app.services.drive_service import DriveService
from app.services.eligibility_service import check_eligibility

router = APIRouter(prefix="/drives", tags=["Drives"])


def _drive_common_fields(drive: Drive, branch_names: list[str]) -> dict:
    return dict(
        id=drive.id,
        company_id=drive.company_id,
        company_name=drive.company.name,
        type_placement_policy=drive.type_placement_policy,
        title=drive.title,
        drive_type=drive.drive_type,
        conversion_type=drive.conversion_type,
        target_graduation_year=drive.target_graduation_year,
        stipend=drive.stipend,
        ctc=drive.ctc,
        location=drive.location,
        ppt_datetime=drive.ppt_datetime,
        oa_datetime=drive.oa_datetime,
        oa_deadline=drive.oa_deadline,
        job_description_url=drive.job_description_url,
        additional_announcements=drive.additional_announcements,
        eligible_branches=branch_names,
    )


async def _resolve_student(
    current_user: User | None, db: AsyncSession
) -> Student | None:
    """Return the caller's Student profile, or None if not a student."""
    if current_user is None or current_user.role != UserRole.STUDENT:
        return None
    return await StudentRepository(db).get_by_user_id(current_user.id)


async def _application_status_for(
    student: Student | None, drive_id: uuid.UUID, db: AsyncSession
) -> str | None:
    if student is None:
        return None
    existing = await ApplicationRepository(db).get_by_student_and_drive(
        student.id, drive_id
    )
    return existing.status.value if existing else None


@router.get(
    "",
    response_model=DriveListResponse,
    summary="List published drives (search, filter, and FOR_ME/ALL feed)",
)
async def list_drives(
    for_me: bool = Query(default=False),
    search: str | None = Query(default=None),
    drive_type: DriveType | None = Query(default=None),
    conversion_type: ConversionType | None = Query(default=None),
    location: str | None = Query(default=None),
    min_ctc: float | None = Query(default=None, ge=0),
    max_ctc: float | None = Query(default=None, ge=0),
    target_graduation_year: int | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DriveListResponse:
    filters = DriveFeedFilter(
        for_me=for_me,
        search=search,
        drive_type=drive_type,
        conversion_type=conversion_type,
        location=location,
        min_ctc=min_ctc,
        max_ctc=max_ctc,
        target_graduation_year=target_graduation_year,
        page=page,
        page_size=page_size,
    )

    student = await _resolve_student(current_user, db)
    service = DriveService(db)
    drives, total = await service.get_drive_feed(filters, student=student)

    items: list[DriveListItem] = []
    for drive in drives:
        branch_names = [b.branch for b in drive.eligible_branches]
        eligibility = None
        if student is not None:
            result = check_eligibility(student, drive, branch_names)
            eligibility = EligibilityResponse(
                status=EligibilityStatus(result.status.value),
                eligible=result.eligible,
                reasons=result.reasons,
            )
        application_status = await _application_status_for(student, drive.id, db)
        items.append(
            DriveListItem(
                **_drive_common_fields(drive, branch_names),
                published_at=drive.published_at,
                eligibility=eligibility,
                application_status=application_status,
            )
        )

    return DriveListResponse(total=total, page=page, page_size=page_size, items=items)


@router.get(
    "/{drive_id}",
    response_model=DriveResponse,
    summary="Get full drive detail, including the caller's eligibility",
)
async def get_drive(
    drive_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DriveResponse:
    student = await _resolve_student(current_user, db)
    service = DriveService(db)
    drive, branch_names, eligibility = await service.get_drive_detail(
        drive_id, student=student
    )
    application_status = await _application_status_for(student, drive.id, db)

    return DriveResponse(
        **_drive_common_fields(drive, branch_names),
        ppt_datetime=drive.ppt_datetime,
        oa_datetime=drive.oa_datetime,
        oa_mode=drive.oa_mode,
        process_mode=drive.process_mode,
        minimum_cgpa=drive.minimum_cgpa,
        maximum_backlogs=drive.maximum_backlogs,
        job_description_url=drive.job_description_url,
        additional_announcements=drive.additional_announcements,
        published=drive.published,
        published_at=drive.published_at,
        created_by=drive.created_by,
        created_at=drive.created_at,
        updated_at=drive.updated_at,
        eligibility=eligibility,
        application_status=application_status,
    )


@router.post(
    "",
    response_model=DriveResponse,
    status_code=201,
    summary="Create a drive (SPC/Admin only). Does not publish it.",
    dependencies=[Depends(require_spc)],
)
async def create_drive(
    request: DriveCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DriveResponse:
    service = DriveService(db)
    drive = await service.create_drive(request, created_by=current_user)
    drive, branch_names, _ = await service.get_drive_detail(drive.id)
    return DriveResponse(
        **_drive_common_fields(drive, branch_names),
        ppt_datetime=drive.ppt_datetime,
        oa_datetime=drive.oa_datetime,
        oa_mode=drive.oa_mode,
        process_mode=drive.process_mode,
        minimum_cgpa=drive.minimum_cgpa,
        maximum_backlogs=drive.maximum_backlogs,
        job_description_url=drive.job_description_url,
        additional_announcements=drive.additional_announcements,
        published=drive.published,
        published_at=drive.published_at,
        created_by=drive.created_by,
        created_at=drive.created_at,
        updated_at=drive.updated_at,
    )


@router.patch(
    "/{drive_id}",
    response_model=DriveResponse,
    summary="Update a drive (SPC/Admin only)",
    dependencies=[Depends(require_spc)],
)
async def update_drive(
    drive_id: uuid.UUID,
    request: DriveUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DriveResponse:
    service = DriveService(db)
    await service.update_drive(drive_id, request, current_user)
    drive, branch_names, _ = await service.get_drive_detail(drive_id)
    return DriveResponse(
        **_drive_common_fields(drive, branch_names),
        ppt_datetime=drive.ppt_datetime,
        oa_datetime=drive.oa_datetime,
        oa_mode=drive.oa_mode,
        process_mode=drive.process_mode,
        minimum_cgpa=drive.minimum_cgpa,
        maximum_backlogs=drive.maximum_backlogs,
        job_description_url=drive.job_description_url,
        additional_announcements=drive.additional_announcements,
        published=drive.published,
        published_at=drive.published_at,
        created_by=drive.created_by,
        created_at=drive.created_at,
        updated_at=drive.updated_at,
    )


@router.post(
    "/{drive_id}/publish",
    response_model=PublishDriveResponse,
    summary="Publish a drive (SPC/Admin only)",
    dependencies=[Depends(require_spc)],
)
async def publish_drive(
    drive_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PublishDriveResponse:
    service = DriveService(db)
    drive = await service.publish_drive(drive_id, current_user)
    return PublishDriveResponse(
        message="Drive published successfully.",
        drive_id=drive.id,
        published_at=drive.published_at,
    )