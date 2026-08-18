"""Audit service — writes audit log entries for sensitive operations."""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


class AuditService:
    """Records important operations to the audit_logs table.

    Never logs authentication tokens, passwords, or sensitive personal data.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def log(
        self,
        action: str,
        entity_type: str,
        user_id: uuid.UUID | None = None,
        entity_id: uuid.UUID | None = None,
        old_value: dict[str, Any] | None = None,
        new_value: dict[str, Any] | None = None,
    ) -> AuditLog:
        """Write a single audit log entry.

        Args:
            action: Human-readable action name (e.g. "DRIVE_PUBLISHED").
            entity_type: Table/domain name (e.g. "drive", "student").
            user_id: UUID of the user performing the action.
            entity_id: UUID of the entity being acted upon.
            old_value: Previous state as JSON-serializable dict (for updates).
            new_value: New state as JSON-serializable dict.

        Returns:
            The persisted AuditLog instance.
        """
        log_entry = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_value=old_value,
            new_value=new_value,
        )
        self.db.add(log_entry)
        await self.db.flush()
        return log_entry
