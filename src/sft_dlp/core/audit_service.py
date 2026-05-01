from __future__ import annotations

from typing import Any

from sft_dlp.db.repositories import AuditLogRepository


class AuditService:
    """High-level wrapper for writing local timestamped audit logs."""

    def __init__(self, audit_repository: AuditLogRepository) -> None:
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
