"""Application repository — database access for the applications table."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.application import Application
from app.models.enums import ApplicationStatus

from app.models.application import Application
from app.models.drive import Drive
from app.models.enums import ApplicationStatus


class ApplicationRepository:
    """Handles all DB queries for the applications table."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_application(
        self,
        student_id: uuid.UUID,
        drive_id: uuid.UUID,
    ) -> Application:
        """Create a new application.

        Note: does NOT catch IntegrityError — that is the responsibility of
        the application_service so it can produce a meaningful 409 response.
        """
        application = Application(
            student_id=student_id,
            drive_id=drive_id,
            status=ApplicationStatus.APPLIED,
        )
        self.db.add(application)
        await self.db.flush()
        await self.db.refresh(application)
        return application

    async def get_application(self, application_id: uuid.UUID) -> Application | None:
        """Fetch an application by its UUID."""
        result = await self.db.execute(
            select(Application).where(Application.id == application_id)
        )
        return result.scalar_one_or_none()

    async def get_by_student_and_drive(
        self, student_id: uuid.UUID, drive_id: uuid.UUID
    ) -> Application | None:
        """Check whether a student has already applied to a drive."""
        result = await self.db.execute(
            select(Application).where(
                Application.student_id == student_id,
                Application.drive_id == drive_id,
            )
        )
        return result.scalar_one_or_none()

    # app/repositories/application_repository.py
    # ADD this method

    async def count_for_drive(self, drive_id: uuid.UUID) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(Application).where(Application.drive_id == drive_id)
        )
        return result.scalar_one()
    

    async def get_student_applications(
        self, student_id: uuid.UUID
    ) -> list[Application]:
        """Return all applications for a student, newest first."""
        result = await self.db.execute(
            select(Application)
            .where(Application.student_id == student_id)
            .options(selectinload(Application.drive).selectinload(Drive.company))
            .order_by(Application.applied_at.desc())
        )
        return list(result.scalars().all())

    async def get_drive_applications(
        self, drive_id: uuid.UUID, page: int = 1, page_size: int = 100
    ) -> tuple[list[Application], int]:
        """Return all applications for a drive (SPC view), paginated."""
        offset = (page - 1) * page_size

        count_result = await self.db.execute(
            select(func.count()).select_from(Application).where(
                Application.drive_id == drive_id
            )
        )
        total = count_result.scalar_one()

        result = await self.db.execute(
            select(Application)
            .where(Application.drive_id == drive_id)
            .options(selectinload(Application.drive).selectinload(Drive.company))

            .order_by(Application.applied_at.asc())
            .offset(offset)
            .limit(page_size)
        )
        applications = list(result.scalars().all())
        return applications, total

    async def update_status(
        self, application: Application, status: ApplicationStatus
    ) -> Application:
        """Update an application's status."""
        application.status = status
        await self.db.flush()
        return application
