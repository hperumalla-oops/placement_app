"""SQLAlchemy model for the students table."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.application import Application

class Student(Base):
    __tablename__ = "students"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    usn: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    branch: Mapped[str] = mapped_column(String, nullable=False)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    graduation_year: Mapped[int] = mapped_column(Integer, nullable=False)
    tenth_percentage: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    twelfth_percentage: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    cgpa: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 2),
        nullable=True,
    )
    backlogs: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )
    resume_url: Mapped[str | None] = mapped_column(String, nullable=True)
    profile_frozen: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )
    cgpa_unlocked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    backlogs_unlocked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "tenth_percentage IS NULL OR (tenth_percentage >= 0 AND tenth_percentage <= 100)",
            name="students_tenth_percentage_check",
        ),
        CheckConstraint(
            "twelfth_percentage IS NULL OR (twelfth_percentage >= 0 AND twelfth_percentage <= 100)",
            name="students_twelfth_percentage_check",
        ),
        CheckConstraint(
            "cgpa IS NULL OR (cgpa >= 0 AND cgpa <= 10)",
            name="students_cgpa_check",
        ),
        CheckConstraint("backlogs >= 0", name="students_backlogs_check"),
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="student")  # noqa: F821
    applications: Mapped[list["Application"]] = relationship(  # noqa: F821
        "Application", back_populates="student"
    )

    def __repr__(self) -> str:
        return f"<Student usn={self.usn} name={self.name}>"
