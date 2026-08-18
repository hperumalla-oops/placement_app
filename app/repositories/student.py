"""Student repository — database access for the students table."""

import uuid
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.student import Student


class StudentRepository:
    """Handles all DB queries for the students table."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, student_id: uuid.UUID) -> Student | None:
        """Fetch a student by their UUID primary key."""
        result = await self.db.execute(
            select(Student).where(Student.id == student_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: uuid.UUID) -> Student | None:
        """Fetch a student by their associated user UUID."""
        result = await self.db.execute(
            select(Student).where(Student.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_usn(self, usn: str) -> Student | None:
        """Fetch a student by USN."""
        result = await self.db.execute(
            select(Student).where(Student.usn == usn)
        )
        return result.scalar_one_or_none()

    async def list_all(self, page: int = 1, page_size: int = 50) -> tuple[list[Student], int]:
        """Return a paginated list of all students plus the total count."""
        offset = (page - 1) * page_size

        count_result = await self.db.execute(select(func.count()).select_from(Student))
        total = count_result.scalar_one()

        result = await self.db.execute(
            select(Student).offset(offset).limit(page_size).order_by(Student.usn)
        )
        students = list(result.scalars().all())
        return students, total

    # async def update_student(self, student: Student, updates: dict) -> Student:
    #     """Apply a dictionary of field updates to a student and flush to DB.

    #     Args:
    #         student: The SQLAlchemy Student instance.
    #         updates: Dict of {field_name: new_value} to apply.

    #     Returns:
    #         The updated Student instance (not yet committed — caller controls tx).
    #     """
    #     for field, value in updates.items():
    #         setattr(student, field, value)
    #     # Refresh the updated_at timestamp
    #     student.updated_at = datetime.utcnow().replace(tzinfo=__import__("datetime").timezone.utc)
    #     await self.db.flush()
    #     return student


    # app/repositories/student_repository.py (wherever update_student lives)
    #   ADD logging around the setattr loop, so we see field-by-field what's applied

    async def update_student(self, student: Student, updates: dict) -> Student:
        print(f"REPO: applying updates = {updates}", flush=True)
        for field, value in updates.items():
            setattr(student, field, value)
            print(f"REPO: after setattr {field}={value!r}, student.{field}={getattr(student, field)!r}", flush=True)
        student.updated_at = datetime.utcnow().replace(tzinfo=__import__("datetime").timezone.utc)
        await self.db.flush()
        print(f"REPO: after flush, student.name={student.name!r} student.backlogs={student.backlogs!r}", flush=True)
        return student

    async def unlock_cgpa(self, student: Student, until: datetime) -> Student:
        """Set the cgpa_unlocked_until timestamp for a student."""
        student.cgpa_unlocked_until = until
        await self.db.flush()
        return student

    async def unlock_backlogs(self, student: Student, until: datetime) -> Student:
        """Set the backlogs_unlocked_until timestamp for a student."""
        student.backlogs_unlocked_until = until
        await self.db.flush()
        return student
