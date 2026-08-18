"""Company routes.

Companies are created once and reused across multiple drives — see spec
section 8. Only SPC/Admin can create or rename a company; students can read.
"""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_spc
from app.core.database import get_db
from app.schemas.company import (
    CompanyCreate,
    CompanyListResponse,
    CompanyResponse,
    CompanyUpdate,
)
from app.services.company_service import CompanyService

router = APIRouter(prefix="/companies", tags=["Companies"])


@router.post(
    "",
    response_model=CompanyResponse,
    status_code=201,
    summary="Create a company (SPC/Admin only)",
    dependencies=[Depends(require_spc)],
)
async def create_company(
    request: CompanyCreate,
    db: AsyncSession = Depends(get_db),
) -> CompanyResponse:
    service = CompanyService(db)
    company = await service.create_company(request.name)
    return CompanyResponse.model_validate(company)


@router.get(
    "",
    response_model=CompanyListResponse,
    summary="List companies",
    dependencies=[Depends(get_current_user)],
)
async def list_companies(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> CompanyListResponse:
    service = CompanyService(db)
    companies, total = await service.list_companies(page=page, page_size=page_size)
    return CompanyListResponse(
        total=total,
        items=[CompanyResponse.model_validate(c) for c in companies],
    )


@router.get(
    "/{company_id}",
    response_model=CompanyResponse,
    summary="Get a company by id",
    dependencies=[Depends(get_current_user)],
)
async def get_company(
    company_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> CompanyResponse:
    service = CompanyService(db)
    company = await service.get_company(company_id)
    return CompanyResponse.model_validate(company)


@router.patch(
    "/{company_id}",
    response_model=CompanyResponse,
    summary="Rename a company (SPC/Admin only)",
    dependencies=[Depends(require_spc)],
)
async def update_company(
    company_id: uuid.UUID,
    request: CompanyUpdate,
    db: AsyncSession = Depends(get_db),
) -> CompanyResponse:
    service = CompanyService(db)
    if request.name is not None:
        company = await service.update_company(company_id, request.name)
    else:
        company = await service.get_company(company_id)
    return CompanyResponse.model_validate(company)