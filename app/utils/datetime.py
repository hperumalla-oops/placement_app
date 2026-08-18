"""Date/time utilities.

All datetimes are timezone-aware UTC. Never use datetime.utcnow() (naive).
The backend is authoritative for time — never trust client-provided timestamps
for deadline/session checks.
"""

from datetime import datetime, timezone


def utcnow() -> datetime:
    """Return the current UTC time as a timezone-aware datetime.

    Use this everywhere instead of datetime.utcnow() which returns naive datetimes.
    """
    return datetime.now(timezone.utc)


def is_deadline_passed(deadline: datetime) -> bool:
    """Check whether a deadline has passed using server time.

    Args:
        deadline: A timezone-aware deadline datetime.

    Returns:
        True if the current UTC time is past the deadline.
    """
    return utcnow() > deadline


def ensure_aware(dt: datetime) -> datetime:
    """Ensure a datetime is timezone-aware (assume UTC if naive).

    Args:
        dt: Any datetime object.

    Returns:
        Timezone-aware datetime in UTC.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt
