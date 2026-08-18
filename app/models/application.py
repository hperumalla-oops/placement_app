"""SQLAlchemy model for the applications table."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ApplicationStatus

if TYPE_CHECKING:
    from app.models.drive import Drive
    from app.models.student import Student


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    # Note: DB schema uses student_id (UUID FK to students.id), not student_usn.
    # The spec's description of using student_usn does not match the actual schema.
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
    )
    drive_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("drives.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[ApplicationStatus] = mapped_column(
        SAEnum(ApplicationStatus, name="application_status", create_type=False),
        nullable=False,
        server_default="APPLIED",
    )
    applied_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("student_id", "drive_id", name="applications_student_id_drive_id_key"),
    )

    # Relationships
    student: Mapped["Student"] = relationship("Student", back_populates="applications")  # noqa: F821
    drive: Mapped["Drive"] = relationship("Drive", back_populates="applications")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Application id={self.id} student_id={self.student_id} drive_id={self.drive_id} status={self.status}>"
