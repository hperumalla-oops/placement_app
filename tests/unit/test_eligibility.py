"""Unit tests for app.services.eligibility_service.check_eligibility.

Pure-Python tests — no database required. Covers every case called out in
the spec (section 35).
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.drive import Drive
from app.models.enums import DriveType
from app.models.student import Student
from app.services.eligibility_service import EligibilityStatus, check_eligibility


def make_student(**overrides) -> Student:
    defaults = dict(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        name="Test Student",
        usn="1XX20CS001",
        branch="CSE",
        graduation_year=2027,
        cgpa=Decimal("8.5"),
        backlogs=0,
    )
    defaults.update(overrides)
    return Student(**defaults)


def make_drive(**overrides) -> Drive:
    defaults = dict(
        id=uuid.uuid4(),
        company_id=uuid.uuid4(),
        title="Test Drive",
        drive_type=DriveType.FULL_TIME_ONLY,
        target_graduation_year=2027,
        oa_deadline=datetime(2030, 1, 1, tzinfo=timezone.utc),
        maximum_backlogs=0,
        minimum_cgpa=None,
    )
    defaults.update(overrides)
    return Drive(**defaults)


def test_eligible_when_all_criteria_met():
    student = make_student(graduation_year=2027, branch="CSE", cgpa=Decimal("9.0"), backlogs=0)
    drive = make_drive(target_graduation_year=2027, minimum_cgpa=Decimal("8.0"), maximum_backlogs=0)

    result = check_eligibility(student, drive, eligible_branch_names=["CSE", "AIML"])

    assert result.status == EligibilityStatus.ELIGIBLE
    assert result.eligible is True
    assert result.reasons == []


def test_wrong_graduation_year_is_not_relevant():
    student = make_student(graduation_year=2028)
    drive = make_drive(target_graduation_year=2027)

    result = check_eligibility(student, drive, eligible_branch_names=[])

    assert result.status == EligibilityStatus.NOT_RELEVANT
    assert result.eligible is False
    assert result.reasons


def test_correct_year_wrong_branch_is_not_eligible():
    student = make_student(graduation_year=2027, branch="MECH")
    drive = make_drive(target_graduation_year=2027)

    result = check_eligibility(student, drive, eligible_branch_names=["CSE", "AIML"])

    assert result.status == EligibilityStatus.NOT_ELIGIBLE
    assert result.eligible is False
    assert any("branch" in r.lower() for r in result.reasons)


def test_cgpa_below_requirement_is_not_eligible():
    student = make_student(graduation_year=2027, cgpa=Decimal("6.5"))
    drive = make_drive(target_graduation_year=2027, minimum_cgpa=Decimal("8.0"))

    result = check_eligibility(student, drive, eligible_branch_names=[])

    assert result.status == EligibilityStatus.NOT_ELIGIBLE
    assert any("cgpa" in r.lower() for r in result.reasons)


def test_backlogs_above_maximum_is_not_eligible():
    student = make_student(graduation_year=2027, backlogs=2)
    drive = make_drive(target_graduation_year=2027, maximum_backlogs=0)

    result = check_eligibility(student, drive, eligible_branch_names=[])

    assert result.status == EligibilityStatus.NOT_ELIGIBLE
    assert any("backlog" in r.lower() for r in result.reasons)


def test_no_cgpa_requirement_does_not_disqualify():
    student = make_student(graduation_year=2027, cgpa=None)
    drive = make_drive(target_graduation_year=2027, minimum_cgpa=None)

    result = check_eligibility(student, drive, eligible_branch_names=[])

    assert result.status == EligibilityStatus.ELIGIBLE


def test_no_branch_restriction_does_not_disqualify():
    student = make_student(graduation_year=2027, branch="MECH")
    drive = make_drive(target_graduation_year=2027)

    result = check_eligibility(student, drive, eligible_branch_names=[])

    assert result.status == EligibilityStatus.ELIGIBLE

def test_multiple_failures_are_all_reported():
    student = make_student(graduation_year=2027, branch="MECH", cgpa=Decimal("5.0"), backlogs=3)
    drive = make_drive(
        target_graduation_year=2027,
        minimum_cgpa=Decimal("8.0"),
        maximum_backlogs=0,
    )

    result = check_eligibility(student, drive, eligible_branch_names=["CSE"])

    assert result.status == EligibilityStatus.NOT_ELIGIBLE
    assert len(result.reasons) == 3


def test_student_profile_patch_route_is_registered():
    client = TestClient(app)
    routes = {route.path: set(route.methods or []) for route in app.routes}

    assert "/students/me" in routes
    assert "PATCH" in routes["/students/me"]