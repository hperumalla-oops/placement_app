"""Company repository — database access for the companies table."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company


class CompanyRepository:
    """Handles all DB queries for the companies table."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, name: str) -> Company:
        """Create a new company.

        Args:
            name: The company's unique name.

        Returns:
            The newly created Company instance (flushed but not committed).
        """
        company = Company(name=name)
        self.db.add(company)
        await self.db.flush()
        await self.db.refresh(company)
        return company

    async def get_by_id(self, company_id: uuid.UUID) -> Company | None:
        """Fetch a company by UUID."""
        result = await self.db.execute(
            select(Company).where(Company.id == company_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Company | None:
        """Fetch a company by exact name (case-sensitive)."""
        result = await self.db.execute(
            select(Company).where(Company.name == name)
        )
        return result.scalar_one_or_none()

    async def list_all(self, page: int = 1, page_size: int = 100) -> tuple[list[Company], int]:
        """Return a paginated list of all companies."""
        offset = (page - 1) * page_size

        count_result = await self.db.execute(select(func.count()).select_from(Company))
        total = count_result.scalar_one()

        result = await self.db.execute(
            select(Company).offset(offset).limit(page_size).order_by(Company.name)
        )
        companies = list(result.scalars().all())
        return companies, total

    async def update(self, company: Company, name: str) -> Company:
        """Update a company's name."""
        company.name = name
        await self.db.flush()
        return company
