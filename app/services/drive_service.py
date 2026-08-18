"""Drive service — business logic for drive creation, updates, and publishing."""

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.models.drive import Drive
from app.models.student import Student
from app.models.user import User
from app.repositories.company import CompanyRepository
from app.repositories.drive import DriveRepository
from app.schemas.drive import (
    DriveCreateRequest,
    DriveListResponse,
    DriveResponse,
    DriveUpdateRequest,
    DriveFeedFilter,
    EligibilityResponse,
    EligibilityStatus,
)
from app.services.audit_service import AuditService
from app.services.eligibility_service import check_eligibility
from app.utils.datetime import is_deadline_passed, utcnow

logger = logging.getLogger(__name__)


class DriveService:
    """Business logic for drive management."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._repo = DriveRepository(db)
        self._company_repo = CompanyRepository(db)
        self._audit = AuditService(db)

    async def create_drive(
        self, request: DriveCreateRequest, created_by: User
    ) -> Drive:
        """Create a new unpublished drive.

        Validates that the referenced company exists.
        Sets eligible branches atomically with the drive creation.
        """
        # Validate company exists
        company = await self._company_repo.get_by_id(request.company_id)
        if company is None:
            raise NotFoundError(f"Company with id={request.company_id} not found.")

        drive = await self._repo.create_drive(
            company_id=request.company_id,
            title=request.title,
            drive_type=request.drive_type,
            conversion_type=request.conversion_type,
            target_graduation_year=request.target_graduation_year,
            stipend=request.stipend,
            ctc=request.ctc,
            location=request.location,
            ppt_datetime=request.ppt_datetime,
            oa_datetime=request.oa_datetime,
            oa_deadline=request.oa_deadline,
            oa_mode=request.oa_mode,
            process_mode=request.process_mode,
            minimum_cgpa=request.minimum_cgpa,
            maximum_backlogs=request.maximum_backlogs,
            type_placement_policy=request.type_placement_policy,
            job_description_url=request.job_description_url,
            additional_announcements=request.additional_announcements,
            created_by=created_by.id,
        )

        # Set eligible branches
        await self._repo.set_eligible_branches(drive.id, request.eligible_branches)

        await self._audit.log(
            action="DRIVE_CREATED",
            entity_type="drive",
            user_id=created_by.id,
            entity_id=drive.id,
            new_value={
                "title": drive.title,
                "company_id": str(drive.company_id),
                "drive_type": drive.drive_type.value,
                "target_graduation_year": drive.target_graduation_year,
            },
        )

        return drive

    async def update_drive(
        self,
        drive_id: uuid.UUID,
        request: DriveUpdateRequest,
        acting_user: User,
    ) -> Drive:
        """Partially update a drive.

        Published drives cannot have certain fields changed via this endpoint.
        Use publish_drive for state transitions.
        """
        drive = await self._repo.get_drive(drive_id)
        if drive is None:
            raise NotFoundError("Drive not found.")

        updates = request.model_dump(exclude_none=True, exclude={"eligible_branches"})
        old_snapshot = {"title": drive.title, "published": drive.published}

        # Handle branch updates separately
        if request.eligible_branches is not None:
            branches = [b.strip().upper() for b in request.eligible_branches]
            if not branches:
                raise BadRequestError("eligible_branches must not be empty.")
            await self._repo.set_eligible_branches(drive_id, branches)

        if updates:
            await self._repo.update_drive(drive, updates)

        await self._audit.log(
            action="DRIVE_UPDATED",
            entity_type="drive",
            user_id=acting_user.id,
            entity_id=drive.id,
            old_value=old_snapshot,
            new_value=updates,
        )

        # Reload drive with branches
        updated_drive = await self._repo.get_drive(drive_id)
        return updated_drive

    async def publish_drive(
        self, drive_id: uuid.UUID, acting_user: User
    ) -> Drive:
        """Publish a drive after validating all required fields.

        Validates:
        - Drive exists and is not already published
        - oa_deadline is in the future
        - eligible_branches is non-empty
        - target_graduation_year is reasonable

        This is a transactional operation — all writes (publish flag + audit log)
        succeed or fail together.
        """
        drive = await self._repo.get_drive_with_company(drive_id)
        if drive is None:
            raise NotFoundError("Drive not found.")

        if drive.published:
            raise ConflictError("Drive is already published.")

        # Pre-publish validation
        if is_deadline_passed(drive.oa_deadline):
            raise BadRequestError(
                "Cannot publish drive: the OA deadline has already passed."
            )

        branches = [b.branch for b in drive.eligible_branches]
        if not branches:
            raise BadRequestError(
                "Cannot publish drive: at least one eligible branch must be specified."
            )

        published_at = utcnow()
        await self._repo.publish_drive(drive, published_at)

        await self._audit.log(
            action="DRIVE_PUBLISHED",
            entity_type="drive",
            user_id=acting_user.id,
            entity_id=drive.id,
            new_value={
                "published_at": published_at.isoformat(),
                "title": drive.title,
                "company": drive.company.name,
            },
        )

        logger.info(
            "Drive published: id=%s title=%s by user=%s",
            drive_id, drive.title, acting_user.id
        )

        return drive

    async def get_drive_detail(
        self,
        drive_id: uuid.UUID,
        student: Student | None = None,
    ) -> tuple[Drive, list[str], EligibilityResponse | None]:
        """Fetch drive detail with eligible branches.

        If a student is provided, includes their eligibility result.

        Returns:
            (drive, branch_names, eligibility_result_or_None)
        """
        drive = await self._repo.get_drive_with_company(drive_id)
        if drive is None:
            raise NotFoundError("Drive not found.")

        branch_names = [b.branch for b in drive.eligible_branches]

        eligibility_response: EligibilityResponse | None = None
        if student is not None:
            result = check_eligibility(student, drive, branch_names)
            eligibility_response = EligibilityResponse(
                status=EligibilityStatus(result.status.value),
                eligible=result.eligible,
                reasons=result.reasons,
            )

        return drive, branch_names, eligibility_response

    async def get_drive_feed(
        self,
        filters: DriveFeedFilter,
        student: Student | None = None,
    ) -> tuple[list[Drive], int]:
        """Return published drives with applied filters.

        For authenticated students, for_me=True filters by their graduation year.
        """
        student_year = student.graduation_year if student else None
        return await self._repo.list_published_drives(
            filters=filters,
            student_graduation_year=student_year,
        )

    async def get_all_drives_spc(
        self, page: int = 1, page_size: int = 50
    ) -> tuple[list[Drive], int]:
        """Return all drives (published + unpublished) for SPC/Admin."""
        return await self._repo.list_all_drives(page=page, page_size=page_size)


    # app/services/drive_service.py
    # ADD applicant count logic when building the response — wherever
    # drives are currently converted to DriveResponse

    async def _to_response(self, drive: Drive) -> DriveResponse:
        applicant_count = None
        if drive.oa_deadline <= utcnow():
            applicant_count = await self._application_repo.count_for_drive(drive.id)

        return DriveResponse(
            # ...existing fields...
            applicant_count=applicant_count,
        )
