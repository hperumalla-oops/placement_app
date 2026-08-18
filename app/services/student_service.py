"""Student service — business logic for student profile management."""

import logging
from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.models.student import Student
from app.models.user import User
from app.repositories.student import StudentRepository
from app.schemas.student import StudentUpdateRequest
from app.services.audit_service import AuditService
from app.utils.datetime import utcnow

logger = logging.getLogger(__name__)


class StudentService:
    """Business logic for student profile reads and updates."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._repo = StudentRepository(db)
        self._audit = AuditService(db)

    async def get_student_profile(self, student_id_or_user_id, by_user_id: bool = True) -> Student:
        """Fetch a student profile, raising 404 if not found.

        Args:
            student_id_or_user_id: Either the student UUID or their user UUID.
            by_user_id: If True, look up by user_id; otherwise by student id.
        """
        import uuid
        if by_user_id:
            student = await self._repo.get_by_user_id(student_id_or_user_id)
        else:
            student = await self._repo.get_by_id(student_id_or_user_id)

        if student is None:
            raise NotFoundError("Student profile not found.")
        return student
    # app/services/student_service.py
    # ADD this method to StudentService

    async def delete_resume(self, student: Student, acting_user: User) -> Student:
        old_snapshot = _student_snapshot(student)
        updated_student = await self._repo.update_student(student, {"resume_url": None})
        await self._audit.log(
            action="STUDENT_RESUME_DELETED",
            entity_type="student",
            user_id=acting_user.id,
            entity_id=student.id,
            old_value=old_snapshot,
            new_value=_student_snapshot(updated_student),
        )
        return updated_student

    async def update_profile(
        self,
        student: Student,
        request: StudentUpdateRequest,
        acting_user: User,
    ) -> Student:
        now = utcnow()
        updates: dict = {}
        old_snapshot = _student_snapshot(student)

        print(f"SERVICE: raw request dict = {request.model_dump()}", flush=True)
        update_data = request.model_dump(exclude_none=True)
        print(f"SERVICE: filtered update_data = {update_data}", flush=True)

        for field, value in update_data.items():

            if field == "resume_url":
                # Always allowed
                updates["resume_url"] = value

            elif field == "cgpa":
                if student.profile_frozen:
                    if student.cgpa_unlocked_until is None or student.cgpa_unlocked_until <= now:
                        raise ForbiddenError(
                            "Your profile is frozen. CGPA can only be updated "
                            "during an SPC-approved unlock window."
                        )
                updates["cgpa"] = value

            elif field == "backlogs":
                if student.profile_frozen:
                    if student.backlogs_unlocked_until is None or student.backlogs_unlocked_until <= now:
                        raise ForbiddenError(
                            "Your profile is frozen. Backlogs can only be updated "
                            "during an SPC-approved unlock window."
                        )
                updates["backlogs"] = value

            else:
                # General profile fields — blocked when frozen
                if student.profile_frozen:
                    raise ForbiddenError(
                        f"Your profile is frozen. Field '{field}' cannot be modified. "
                        "Please contact SPC for assistance."
                    )
                updates[field] = value

        if not updates:
            return student

        updated_student = await self._repo.update_student(student, updates)


        update_data = request.model_dump(exclude_none=True)
        print(f"SERVICE: filtered update_data = {update_data}", flush=True)

        # Audit log for academic field changes
        sensitive_fields = {"cgpa", "backlogs", "tenth_percentage", "twelfth_percentage"}
        if sensitive_fields & set(updates.keys()):
            await self._audit.log(
                action="STUDENT_ACADEMIC_UPDATE",
                entity_type="student",
                user_id=acting_user.id,
                entity_id=student.id,
                old_value=old_snapshot,
                new_value=_student_snapshot(updated_student),
            )

        return updated_student

    async def unlock_cgpa(
        self,
        student_id,
        unlock_hours: int,
        acting_user: User,
    ) -> Student:
        """SPC operation: temporarily unlock a student's CGPA for editing."""
        student = await self._repo.get_by_id(student_id)
        if student is None:
            raise NotFoundError("Student not found.")

        until = utcnow() + timedelta(hours=unlock_hours)
        updated = await self._repo.unlock_cgpa(student, until)

        await self._audit.log(
            action="CGPA_UNLOCK",
            entity_type="student",
            user_id=acting_user.id,
            entity_id=student.id,
            new_value={"cgpa_unlocked_until": until.isoformat(), "unlock_hours": unlock_hours},
        )

        return updated

    async def unlock_backlogs(
        self,
        student_id,
        unlock_hours: int,
        acting_user: User,
    ) -> Student:
        """SPC operation: temporarily unlock a student's backlog count for editing."""
        student = await self._repo.get_by_id(student_id)
        if student is None:
            raise NotFoundError("Student not found.")

        until = utcnow() + timedelta(hours=unlock_hours)
        updated = await self._repo.unlock_backlogs(student, until)

        await self._audit.log(
            action="BACKLOGS_UNLOCK",
            entity_type="student",
            user_id=acting_user.id,
            entity_id=student.id,
            new_value={"backlogs_unlocked_until": until.isoformat(), "unlock_hours": unlock_hours},
        )

        return updated


def _student_snapshot(student: Student) -> dict:
    """Create a JSON-serializable snapshot of a student's academic fields for audit logs."""
    return {
        "cgpa": str(student.cgpa) if student.cgpa is not None else None,
        "backlogs": student.backlogs,
        "tenth_percentage": str(student.tenth_percentage) if student.tenth_percentage else None,
        "twelfth_percentage": str(student.twelfth_percentage) if student.twelfth_percentage else None,
        "profile_frozen": student.profile_frozen,
    }
