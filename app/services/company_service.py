"""Company service — business logic for company management."""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.company import Company
from app.repositories.company import CompanyRepository

logger = logging.getLogger(__name__)


class CompanyService:
    """Business logic for creating and managing companies."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._repo = CompanyRepository(db)

    async def create_company(self, name: str) -> Company:
        """Create a new company, rejecting duplicates.

        Args:
            name: The company's display name (must be unique).

        Returns:
            The newly created Company.

        Raises:
            ConflictError: If a company with this name already exists.
        """
        existing = await self._repo.get_by_name(name)
        if existing is not None:
            raise ConflictError(
                f"A company named '{name}' already exists.",
                detail=f"Use the existing company (id={existing.id}) when creating drives.",
            )
        return await self._repo.create(name)

    async def get_company(self, company_id) -> Company:
        """Fetch a company by UUID, raising 404 if not found."""
        company = await self._repo.get_by_id(company_id)
        if company is None:
            raise NotFoundError("Company not found.")
        return company

    async def list_companies(self, page: int = 1, page_size: int = 100) -> tuple[list[Company], int]:
        """Return a paginated list of all companies."""
        return await self._repo.list_all(page=page, page_size=page_size)

    async def update_company(self, company_id, name: str) -> Company:
        """Update a company's name.

        Raises:
            NotFoundError: If the company does not exist.
            ConflictError: If the new name is taken by another company.
        """
        company = await self._repo.get_by_id(company_id)
        if company is None:
            raise NotFoundError("Company not found.")

        if company.name != name:
            existing = await self._repo.get_by_name(name)
            if existing is not None and existing.id != company.id:
                raise ConflictError(f"A company named '{name}' already exists.")

        return await self._repo.update(company, name)
