"""SQLAlchemy models for the drives and drive_eligible_branches tables."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ConversionType, DriveType, OAMode, ProcessMode

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.drive import Drive
    from app.models.company import Company
    from app.models.application import Application


class Drive(Base):
    __tablename__ = "drives"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    drive_type: Mapped[DriveType] = mapped_column(
        SAEnum(DriveType, name="drive_type", create_type=False),
        nullable=False,
    )
    conversion_type: Mapped[ConversionType | None] = mapped_column(
        SAEnum(ConversionType, name="conversion_type", create_type=False),
        nullable=True,
    )
    target_graduation_year: Mapped[int] = mapped_column(Integer, nullable=False)
    stipend: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    ctc: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    location: Mapped[str | None] = mapped_column(String, nullable=True)
    ppt_datetime: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    oa_datetime: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    oa_deadline: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    oa_mode: Mapped[OAMode | None] = mapped_column(
        SAEnum(OAMode, name="oa_mode", create_type=False),
        nullable=True,
    )
    process_mode: Mapped[ProcessMode | None] = mapped_column(
        SAEnum(ProcessMode, name="process_mode", create_type=False),
        nullable=True,
    )
    minimum_cgpa: Mapped[Decimal | None] = mapped_column(Numeric(4, 2), nullable=True)
    maximum_backlogs: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    type_placement_policy: Mapped[str | None] = mapped_column(
        "Type_placement_policy", Text, nullable=True
    )
    job_description_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    additional_announcements: Mapped[str | None] = mapped_column(Text, nullable=True)
    published: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "minimum_cgpa IS NULL OR (minimum_cgpa >= 0 AND minimum_cgpa <= 10)",
            name="drives_minimum_cgpa_check",
        ),
        CheckConstraint("maximum_backlogs >= 0", name="drives_maximum_backlogs_check"),
        CheckConstraint("stipend IS NULL OR stipend >= 0", name="drives_stipend_check"),
        CheckConstraint("ctc IS NULL OR ctc >= 0", name="drives_ctc_check"),
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="drives")  # noqa: F821
    eligible_branches: Mapped[list["DriveEligibleBranch"]] = relationship(
        "DriveEligibleBranch",
        back_populates="drive",
        cascade="all, delete-orphan",
    )
    applications: Mapped[list["Application"]] = relationship(  # noqa: F821
        "Application", back_populates="drive"
    )

    def __repr__(self) -> str:
        return f"<Drive id={self.id} title={self.title}>"


class DriveEligibleBranch(Base):
    __tablename__ = "drive_eligible_branches"

    drive_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("drives.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    branch: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)

    # Relationships
    drive: Mapped["Drive"] = relationship("Drive", back_populates="eligible_branches")

    def __repr__(self) -> str:
        return f"<DriveEligibleBranch drive_id={self.drive_id} branch={self.branch}>"
