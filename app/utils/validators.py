"""Field-level validation utilities used across services and schemas."""

from datetime import datetime, timezone


def validate_graduation_year(year: int) -> int:
    """Validate that a graduation year is within a realistic range.

    Args:
        year: The graduation year to validate.

    Returns:
        The validated year.

    Raises:
        ValueError: If the year is outside the acceptable range.
    """
    current_year = datetime.now(timezone.utc).year
    min_year = current_year - 1  # Allow one year in the past (for recent graduates)
    max_year = current_year + 6  # Max 6 years ahead

    if not (min_year <= year <= max_year):
        raise ValueError(
            f"graduation_year must be between {min_year} and {max_year}. Got: {year}"
        )
    return year


def validate_cgpa(cgpa: float) -> float:
    """Validate CGPA is within 0–10 range.

    Args:
        cgpa: The CGPA value.

    Returns:
        The validated CGPA.

    Raises:
        ValueError: If CGPA is out of range.
    """
    if not (0 <= cgpa <= 10):
        raise ValueError(f"CGPA must be between 0 and 10. Got: {cgpa}")
    return cgpa


def validate_percentage(pct: float, field_name: str = "percentage") -> float:
    """Validate a percentage value is within 0–100.

    Args:
        pct: The percentage value.
        field_name: Human-readable name for error messages.

    Returns:
        The validated percentage.

    Raises:
        ValueError: If percentage is out of range.
    """
    if not (0 <= pct <= 100):
        raise ValueError(f"{field_name} must be between 0 and 100. Got: {pct}")
    return pct


def validate_backlogs(backlogs: int) -> int:
    """Validate backlog count is non-negative.

    Args:
        backlogs: Backlog count.

    Returns:
        The validated count.

    Raises:
        ValueError: If backlogs is negative.
    """
    if backlogs < 0:
        raise ValueError(f"Backlogs must be >= 0. Got: {backlogs}")
    return backlogs
