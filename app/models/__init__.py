"""Model package — exposes all models and enums for convenient imports."""

from app.models.enums import (
    ApplicationStatus,
    ConversionType,
    DriveType,
    OAMode,
    ProcessMode,
    UserRole,
)
from app.models.user import User
from app.models.student import Student
from app.models.company import Company
from app.models.drive import Drive, DriveEligibleBranch
from app.models.application import Application
from app.models.audit_log import AuditLog

__all__ = [
    "User",
    "Student",
    "Company",
    "Drive",
    "DriveEligibleBranch",
    "Application",
    "AuditLog",
    "UserRole",
    "DriveType",
    "ConversionType",
    "ApplicationStatus",
    "OAMode",
    "ProcessMode",
]
