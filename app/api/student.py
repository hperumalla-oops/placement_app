"""Student profile routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_student, get_current_user
from app.core.database import get_db
from app.models.student import Student
from app.models.user import User
from app.schemas.student import StudentResponse, StudentUpdateRequest
from app.services.student_service import StudentService

router = APIRouter(prefix="/students", tags=["Students"])


@router.get(
    "/me",
    response_model=StudentResponse,
    summary="Get the authenticated student's profile",
)
async def get_my_profile(student: Student = Depends(get_current_student)) -> Student:
    return student


@router.patch(
    "/me",
    response_model=StudentResponse,
    summary="Update the authenticated student's profile",
    description=(
        "Resume can always be updated. CGPA/backlogs can only be updated while "
        "SPC has temporarily unlocked them. Other fields are frozen once "
        "profile_frozen=true."
    ),
)
async def update_my_profile(
    request: StudentUpdateRequest,
    student: Student = Depends(get_current_student),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Student:
    service = StudentService(db)
    return await service.update_profile(student, request, current_user)


@router.delete(
    "/me/resume",
    response_model=StudentResponse,
    summary="Remove the authenticated student's resume",
)
async def delete_my_resume(
    student: Student = Depends(get_current_student),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Student:
    service = StudentService(db)
    return await service.delete_resume(student, current_user)