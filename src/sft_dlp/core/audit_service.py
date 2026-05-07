from __future__ import annotations

from typing import Any

from sft_dlp.db.repositories import AuditLogRepository


class AuditService:
    """High-level wrapper for writing local timestamped audit logs."""

    def __init__(self, audit_repository: AuditLogRepository) -> None:
        """Initialize audit service.

        Args:
            audit_repository: Repository used to persist audit events.

        Returns:
            None.
        """
        self._audit_repository = audit_repository

    def log(
        self,
        event_type: str,
        actor: str,
        status: str,
        message: str,
        *,
        file_id: int | None = None,
        recipient_id: int | None = None,
        share_id: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Write an audit event to local storage.

        Args:
            event_type: Normalized event identifier.
            actor: User or system actor name.
            status: Event status (`success`, `warning`, `blocked`, `error`).
            message: Human-readable event details.
            file_id: Optional related file id.
            recipient_id: Optional related recipient id.
            share_id: Optional related share id.
            metadata: Optional structured metadata payload.

        Returns:
            None.
        """
        self._audit_repository.log_event(
            event_type=event_type,
            actor=actor,
            status=status,
            message=message,
            file_id=file_id,
            recipient_id=recipient_id,
            share_id=share_id,
            metadata=metadata,
        )
