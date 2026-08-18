"""Drive repository — database access for drives and drive_eligible_branches."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.drive import Drive, DriveEligibleBranch
from app.models.enums import ConversionType, DriveType, OAMode, ProcessMode
from app.schemas.drive import DriveFeedFilter


class DriveRepository:
    """Handles all DB queries for drives and eligible branches."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_drive(
        self,
        company_id: uuid.UUID,
        title: str,
        drive_type: DriveType,
        target_graduation_year: int,
        oa_deadline: datetime,
        maximum_backlogs: int,
        created_by: uuid.UUID | None = None,
        conversion_type: ConversionType | None = None,
        stipend: Decimal | None = None,
        ctc: Decimal | None = None,
        location: str | None = None,
        ppt_datetime: datetime | None = None,
        oa_datetime: datetime | None = None,
        oa_mode: OAMode | None = None,
        process_mode: ProcessMode | None = None,
        minimum_cgpa: Decimal | None = None,
        type_placement_policy: str | None = None,
        job_description_url: str | None = None,
        additional_announcements: str | None = None,
    ) -> Drive:
        """Create a new drive (unpublished by default)."""
        drive = Drive(
            company_id=company_id,
            title=title,
            drive_type=drive_type,
            conversion_type=conversion_type,
            target_graduation_year=target_graduation_year,
            stipend=stipend,
            ctc=ctc,
            location=location,
            ppt_datetime=ppt_datetime,
            oa_datetime=oa_datetime,
            oa_deadline=oa_deadline,
            oa_mode=oa_mode,
            process_mode=process_mode,
            minimum_cgpa=minimum_cgpa,
            maximum_backlogs=maximum_backlogs,
            type_placement_policy=type_placement_policy,
            job_description_url=job_description_url,
            additional_announcements=additional_announcements,
            created_by=created_by,
            published=False,
        )
        self.db.add(drive)
        await self.db.flush()
        await self.db.refresh(drive)
        return drive

    async def get_drive(
        self, drive_id: uuid.UUID, load_branches: bool = True
    ) -> Drive | None:
        """Fetch a drive by UUID, optionally eager-loading eligible branches."""
        query = select(Drive).where(Drive.id == drive_id)
        if load_branches:
            query = query.options(selectinload(Drive.eligible_branches))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_drive_with_company(self, drive_id: uuid.UUID) -> Drive | None:
        """Fetch a drive along with its company and eligible branches."""
        from app.models.company import Company
        query = (
            select(Drive)
            .where(Drive.id == drive_id)
            .options(
                selectinload(Drive.eligible_branches),
                selectinload(Drive.company),
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_published_drives(
        self, filters: DriveFeedFilter, student_graduation_year: int | None = None
    ) -> tuple[list[Drive], int]:
        """Return published drives matching the given filters."""
        from app.models.company import Company

        base_query = (
            select(Drive)
            .join(Drive.company)
            .where(Drive.published == True)  # noqa: E712
            .options(
                selectinload(Drive.eligible_branches),
                selectinload(Drive.company),
            )
        )

        # FOR_ME: filter by student's own graduation year
        if filters.for_me and student_graduation_year:
            base_query = base_query.where(
                Drive.target_graduation_year == student_graduation_year
            )

        # Explicit graduation year filter
        if filters.target_graduation_year:
            base_query = base_query.where(
                Drive.target_graduation_year == filters.target_graduation_year
            )

        # Text search across company name and drive title
        if filters.search:
            search_term = f"%{filters.search}%"
            base_query = base_query.where(
                or_(
                    Company.name.ilike(search_term),
                    Drive.title.ilike(search_term),
                )
            )

        if filters.drive_type:
            base_query = base_query.where(Drive.drive_type == filters.drive_type)

        if filters.conversion_type:
            base_query = base_query.where(Drive.conversion_type == filters.conversion_type)

        if filters.location:
            base_query = base_query.where(Drive.location.ilike(f"%{filters.location}%"))

        if filters.min_ctc is not None:
            base_query = base_query.where(Drive.ctc >= filters.min_ctc)

        if filters.max_ctc is not None:
            base_query = base_query.where(Drive.ctc <= filters.max_ctc)

        if filters.oa_from:
            base_query = base_query.where(Drive.oa_deadline >= filters.oa_from)

        if filters.oa_to:
            base_query = base_query.where(Drive.oa_deadline <= filters.oa_to)

        if filters.published_from:
            base_query = base_query.where(Drive.published_at >= filters.published_from)

        # Count total before pagination
        count_query = select(func.count()).select_from(base_query.subquery())
        count_result = await self.db.execute(count_query)
        total = count_result.scalar_one()

        # Apply pagination
        offset = (filters.page - 1) * filters.page_size
        paginated_query = (
            base_query
            .order_by(Drive.published_at.desc())
            .offset(offset)
            .limit(filters.page_size)
        )
        result = await self.db.execute(paginated_query)
        drives = list(result.scalars().all())
        return drives, total

    async def list_all_drives(
        self, page: int = 1, page_size: int = 50
    ) -> tuple[list[Drive], int]:
        """Return ALL drives (published + unpublished) for SPC/Admin."""
        offset = (page - 1) * page_size

        count_result = await self.db.execute(select(func.count()).select_from(Drive))
        total = count_result.scalar_one()

        result = await self.db.execute(
            select(Drive)
            .options(selectinload(Drive.eligible_branches), selectinload(Drive.company))
            .order_by(Drive.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        drives = list(result.scalars().all())
        return drives, total

    async def update_drive(self, drive: Drive, updates: dict) -> Drive:
        """Apply a dictionary of updates to a drive and flush."""
        for field, value in updates.items():
            setattr(drive, field, value)
        await self.db.flush()
        return drive

    async def publish_drive(self, drive: Drive, published_at: datetime) -> Drive:
        """Mark a drive as published."""
        drive.published = True
        drive.published_at = published_at
        await self.db.flush()
        return drive

    async def get_eligible_branches(self, drive_id: uuid.UUID) -> list[str]:
        """Return branch names for a drive."""
        result = await self.db.execute(
            select(DriveEligibleBranch.branch).where(
                DriveEligibleBranch.drive_id == drive_id
            )
        )
        return list(result.scalars().all())

    async def set_eligible_branches(
        self, drive_id: uuid.UUID, branches: list[str]
    ) -> None:
        """Replace the eligible branches for a drive entirely.

        Deletes existing branches and inserts the new set.
        """
        # Delete existing
        existing = await self.db.execute(
            select(DriveEligibleBranch).where(DriveEligibleBranch.drive_id == drive_id)
        )
        for row in existing.scalars().all():
            await self.db.delete(row)

        # Insert new
        for branch in branches:
            self.db.add(DriveEligibleBranch(drive_id=drive_id, branch=branch.strip().upper()))

        await self.db.flush()
