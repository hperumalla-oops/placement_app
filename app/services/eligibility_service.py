"""Eligibility engine — determines a student's eligibility for a drive.

This is a pure-Python service with no database dependencies.
It is called by both the explicit eligibility endpoint and the application
endpoint (server-side re-check before creating an application).

The engine returns a structured result with:
- status: ELIGIBLE | NOT_ELIGIBLE | NOT_RELEVANT
- eligible: bool shortcut
- reasons: human-readable list of disqualification reasons
"""

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum

from app.models.drive import Drive, DriveEligibleBranch
from app.models.student import Student


class EligibilityStatus(str, Enum):
    """Three-way eligibility status."""
    ELIGIBLE = "ELIGIBLE"
    NOT_ELIGIBLE = "NOT_ELIGIBLE"
    NOT_RELEVANT = "NOT_RELEVANT"  # Student is from a different graduation batch


@dataclass
class EligibilityResult:
    """Structured result from the eligibility engine."""

    status: EligibilityStatus
    eligible: bool
    reasons: list[str] = field(default_factory=list)

    @classmethod
    def eligible_result(cls) -> "EligibilityResult":
        return cls(status=EligibilityStatus.ELIGIBLE, eligible=True, reasons=[])

    @classmethod
    def not_relevant(cls, reasons: list[str]) -> "EligibilityResult":
        return cls(status=EligibilityStatus.NOT_RELEVANT, eligible=False, reasons=reasons)

    @classmethod
    def not_eligible(cls, reasons: list[str]) -> "EligibilityResult":
        return cls(status=EligibilityStatus.NOT_ELIGIBLE, eligible=False, reasons=reasons)


def check_eligibility(
    student: Student,
    drive: Drive,
    eligible_branch_names: list[str],
) -> EligibilityResult:
    """Evaluate whether a student is eligible to apply to a drive.

    Checks are performed in order of specificity:
    1. Graduation year → NOT_RELEVANT if mismatched (wrong batch)
    2. Branch, CGPA, backlogs → NOT_ELIGIBLE if failed

    Args:
        student: The Student model instance.
        drive: The Drive model instance.
        eligible_branch_names: List of branch strings for the drive.

    Returns:
        An EligibilityResult with status, eligible flag, and reason list.
    """
    # ── Step 1: Graduation Year ───────────────────────────────────────────────
    # Mismatch → NOT_RELEVANT (student is from a different batch)
    if student.graduation_year != drive.target_graduation_year:
        return EligibilityResult.not_relevant([
            f"This drive is intended for the {drive.target_graduation_year} graduating batch. "
            f"You are in the {student.graduation_year} batch."
        ])

    # ── Steps 2–4: Branch, CGPA, Backlogs → NOT_ELIGIBLE ─────────────────────
    reasons: list[str] = []

    # Branch check (only if drive specifies branch restrictions)
    if eligible_branch_names:
        normalized_student_branch = (student.branch or "").strip().upper()
        normalized_branches = [b.strip().upper() for b in eligible_branch_names]
        if normalized_student_branch not in normalized_branches:
            branch_list = ", ".join(normalized_branches)
            reasons.append(
                f"Required branch: {branch_list}. Your branch is {student.branch}."
            )

    # CGPA check (only if drive specifies a minimum)
    if drive.minimum_cgpa is not None:
        if student.cgpa is None:
            reasons.append(
                f"Minimum CGPA is {drive.minimum_cgpa}. Your CGPA has not been set."
            )
        elif student.cgpa < drive.minimum_cgpa:
            reasons.append(
                f"Minimum CGPA is {drive.minimum_cgpa}. Your CGPA is {student.cgpa}."
            )

    # Backlog check
    if student.backlogs > drive.maximum_backlogs:
        reasons.append(
            f"Maximum allowed backlogs: {drive.maximum_backlogs}. "
            f"You have {student.backlogs} backlog(s)."
        )

    if reasons:
        return EligibilityResult.not_eligible(reasons)

    return EligibilityResult.eligible_result()
