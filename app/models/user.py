"""SQLAlchemy model for the users table.

Maps to the existing PostgreSQL schema. The user_role enum is a native
PostgreSQL enum — we use create_type=False since it already exists.
"""

import uuid
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SAEnum, String, DateTime

from app.core.database import Base
from app.models.enums import UserRole

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.audit_log import AuditLog
    from app.models.student import Student

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role", create_type=False),
        nullable=False,
        server_default="STUDENT",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )

    # Relationships
    student: Mapped["Student"] = relationship("Student", back_populates="user", uselist=False)  # noqa: F821
    audit_logs: Mapped[list["AuditLog"]] = relationship("AuditLog", back_populates="user")  # noqa: F821

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role}>"
