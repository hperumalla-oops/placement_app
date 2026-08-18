"""Application service — business logic for the student application flow.

The full flow (per spec section 16) is enforced server-side:
1. Verify drive exists and is published
2. Verify OA deadline has not passed (using server time)
3. Check student has not already applied
4. Run eligibility engine
5. Create application (catching DB-level duplicate constraint)
6. Write audit log
"""

import logging
import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.models.application import Application
from app.models.student import Student
from app.models.user import User
from app.repositories.application import ApplicationRepository
from app.repositories.drive import DriveRepository
from app.services.audit_service import AuditService
from app.services.eligibility_service import EligibilityStatus, check_eligibility
from app.utils.datetime import is_deadline_passed
from app.schemas.application import ApplicationCreateRequest

logger = logging.getLogger(__name__)


class ApplicationService:
    """Orchestrates the full application flow for a student."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._app_repo = ApplicationRepository(db)
        self._drive_repo = DriveRepository(db)
        self._audit = AuditService(db)

    async def apply_to_drive(
        self,
        student: Student,
        drive_id: uuid.UUID,
        acting_user: User,
    ) -> Application:
        """Run the full application flow and create an application.

        Args:
            student: The authenticated student applying.
            drive_id: The drive to apply to.
            acting_user: The User record for the student (for audit logging).

        Returns:
            The created Application.

        Raises:
            NotFoundError: If the drive doesn't exist.
            BadRequestError: If the drive is unpublished, deadline passed, or
                             student is not eligible.
            ConflictError: If the student has already applied (including
                           concurrent duplicate requests caught at DB level).
        """

       # Step 1–5: Retrieve and validate the drive.
        # Uses get_drive_with_company (not get_drive) so that drive.company is
        # already loaded — the API layer builds the response from this same
        # object and must never trigger a lazy load in the async session.
        drive = await self._drive_repo.get_drive_with_company(drive_id)
        drive = await self._drive_repo.get_drive(drive_id, load_branches=True)
        if drive is None:
            raise NotFoundError("Drive not found.")

        # Step 6: Drive must be published
        if not drive.published:
            raise BadRequestError("This drive is not currently open for applications.")

        # Step 7: Deadline must not have passed (server time is authoritative)
        if is_deadline_passed(drive.oa_deadline):
            raise BadRequestError(
                "The application deadline for this drive has passed. "
                "No further applications are accepted."
            )

        # Step 8: Check for existing application (optimistic — DB constraint is authoritative)
        existing = await self._app_repo.get_by_student_and_drive(student.id, drive_id)
        if existing is not None:
            raise ConflictError(
                "You have already applied to this drive.",
                detail=f"Existing application id: {existing.id}",
            )

        # Step 9: Run eligibility engine
        branch_names = [b.branch for b in drive.eligible_branches]
        if student.resume_url is None:
            raise ForbiddenError("Please upload your resume before applying.")
        
        eligibility_result = check_eligibility(student, drive, branch_names)

        # Step 10: Reject if not eligible
        if not eligibility_result.eligible:
            reason_text = " | ".join(eligibility_result.reasons)
            raise BadRequestError(
                "You are not eligible for this drive.",
                detail=reason_text,
            )

        # Step 11: Create application — catch DB-level duplicate (concurrent requests)
        try:
            application = await self._app_repo.create_application(
                student_id=student.id,
                drive_id=drive_id,
            )
        except IntegrityError:
            await self.db.rollback()
            logger.warning(
                "Duplicate application caught at DB level: student_id=%s drive_id=%s",
                student.id, drive_id,
            )
            raise ConflictError(
                "You have already applied to this drive.",
                detail="Duplicate request detected.",
            )
                 # Attach the already-loaded drive (with company) onto the new
        # application in-memory so the API layer can build a response
        # without triggering a lazy load on the async session.
        application.drive = drive

        # Step 12: Audit log
        await self._audit.log(
            action="APPLICATION_CREATED",
            entity_type="application",
            user_id=acting_user.id,
            entity_id=application.id,
            new_value={
                "student_id": str(student.id),
                "drive_id": str(drive_id),
                "status": application.status.value,
            },
        )

        logger.info(
            "Application created: student_id=%s drive_id=%s application_id=%s",
            student.id, drive_id, application.id,
        )

        return application

    async def get_student_applications(self, student: Student) -> list[Application]:
        """Return all applications for the authenticated student."""
        return await self._app_repo.get_student_applications(student.id)

    async def get_drive_applications(
        self,
        drive_id: uuid.UUID,
        page: int = 1,
        page_size: int = 100,
    ) -> tuple[list[Application], int]:
        """Return applications for a drive (SPC view)."""
        # Verify drive exists
        drive = await self._drive_repo.get_drive(drive_id, load_branches=False)
        if drive is None:
            raise NotFoundError("Drive not found.")

        return await self._app_repo.get_drive_applications(
            drive_id=drive_id, page=page, page_size=page_size
        )

    # app/services/application_service.py
# ADD this method — enforces the checkbox server-side, never trust client-only validation

    async def apply(
        self,
        student: Student,
        request: ApplicationCreateRequest,
        acting_user: User,
    ) -> Application:
        if not request.confirmed_details_accurate:
            raise ValidationError(
                "You must confirm your details are accurate before applying."
            )

        if student.resume_url is None:
            raise ForbiddenError("Please upload your resume before applying.")

        drive = await self._drive_repo.get_by_id(request.drive_id)
        if drive is None or not drive.published:
            raise NotFoundError("This drive is not available.")

        existing = await self._repo.get_by_student_and_drive(student.id, drive.id)
        if existing is not None:
            raise ConflictError("You've already applied to this drive.")

        eligibility = EligibilityEngine.evaluate(student, drive)
        if not eligibility.eligible:
            raise ForbiddenError(eligibility.reason or "You are not eligible for this drive.")

        if drive.oa_deadline <= utcnow():
            raise ForbiddenError("Applications for this drive have closed.")

        application = await self._repo.create(
            student_id=student.id,
            drive_id=drive.id,
            status=ApplicationStatus.APPLIED,
        )

        await self._audit.log(
            action="APPLICATION_SUBMITTED",
            entity_type="application",
            user_id=acting_user.id,
            entity_id=application.id,
            old_value=None,
            new_value={"drive_id": str(drive.id), "status": "APPLIED"},
        )

        return application

    