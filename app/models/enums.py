"""Python enum definitions mirroring the PostgreSQL native enums.

These are used in SQLAlchemy models (native_enum=True, create_type=False)
and in Pydantic schemas. The string values must exactly match the PostgreSQL
enum values, including the special '6_MONTH_FTE/PBC' value.
"""

import enum


class UserRole(str, enum.Enum):
    STUDENT = "STUDENT"
    SPC = "SPC"
    ADMIN = "ADMIN"


class DriveType(str, enum.Enum):
    SUMMER_INTERNSHIP = "SUMMER_INTERNSHIP"
    FULL_TIME = "FULL_TIME"
    INTERNSHIP_PLUS_FULL_TIME = "INTERNSHIP_PLUS_FULL_TIME"


class ConversionType(str, enum.Enum):
    PBC = "PBC"
    FTE = "FTE"
    SIX_MONTH_PBC = "SIX_MONTH_PBC"
    SIX_MONTH_FTE = "SIX_MONTH_FTE"
    SIX_MONTH_FTE_OR_PBC = "6_MONTH_FTE/PBC"  # Contains '/' — handled as native PG enum
    INTERNSHIP_ONLY = "INTERNSHIP_ONLY"


class ApplicationStatus(str, enum.Enum):
    APPLIED = "APPLIED"
    OA_SHORTLISTED = "OA_SHORTLISTED"
    INTERVIEW_SHORTLISTED = "INTERVIEW_SHORTLISTED"
    SELECTED = "SELECTED"
    REJECTED = "REJECTED"


class OAMode(str, enum.Enum):
    VIRTUAL = "VIRTUAL"
    IN_PERSON = "IN_PERSON"


class ProcessMode(str, enum.Enum):
    VIRTUAL = "VIRTUAL"
    IN_PERSON = "IN_PERSON"
    HYBRID = "HYBRID"
