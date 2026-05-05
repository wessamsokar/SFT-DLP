from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from sft_dlp.config import BASE_DIR
from sft_dlp.core.audit_service import AuditService
from sft_dlp.core.dlp_engine import DlpPolicyEngine
from sft_dlp.core.encryption_engine import FileEncryptionEngine
from sft_dlp.db.repositories import RecipientRepository, ShareRepository
from sft_dlp.utils.file_utils import validate_path_within_base


@dataclass
class ShareResult:
    """Result payload for newly created secure share links.

    Attributes:
        share_id: Share record identifier.
        share_link: Generated link carrying secure token.
        expires_at: Expiration timestamp string in UTC.
        file_id: Related encrypted file identifier.
    """

    share_id: int
    share_link: str
    expires_at: str
    file_id: int


class SecureSharingService:
    """Creates local encrypted share links with DLP checks and expiration."""

    def __init__(
        self,
        recipient_repository: RecipientRepository,
        share_repository: ShareRepository,
        encryption_engine: FileEncryptionEngine,
        dlp_engine: DlpPolicyEngine,
        audit_service: AuditService,
    ) -> None:
        self._recipient_repository = recipient_repository
        self._share_repository = share_repository
        self._encryption_engine = encryption_engine
        self._dlp_engine = dlp_engine
        self._audit_service = audit_service

    def create_share(
        self,
        *,
        file_path: Path,
        output_dir: Path,
        recipient_name: str,
        recipient_email: str,
        recipient_authorized: bool,
        expires_in_hours: int,
        actor: str,
    ) -> ShareResult:
        """Create an encrypted share after DLP and recipient policy checks.

        Args:
            file_path: Source file requested for sharing.
            output_dir: Destination directory for encrypted file output.
            recipient_name: Display name for recipient.
            recipient_email: Recipient email used for policy checks.
            recipient_authorized: Trust status for recipient.
            expires_in_hours: Link validity duration in hours.
            actor: User identifier used in audit logs.

        Returns:
            Share creation result containing tokenized link metadata.
        """
        file_path = validate_path_within_base(file_path, base_dir=BASE_DIR)
        output_dir = validate_path_within_base(output_dir, base_dir=BASE_DIR)
        recipient = self._recipient_repository.upsert_recipient(
            name=recipient_name,
            email=recipient_email,
            is_authorized=recipient_authorized,
        )

        dlp_decision = self._dlp_engine.evaluate_file_transfer(
            file_path=file_path,
            recipient=recipient,
            actor=actor,
        )
        if dlp_decision.is_blocked:
            self._audit_service.log(
                event_type="share_blocked",
                actor=actor,
                status="blocked",
                message=f"Sharing blocked by DLP rule: {dlp_decision.matched_rule_name}",
                recipient_id=recipient.recipient_id,
                metadata={"file_path": str(file_path)},
            )
            raise PermissionError(
                f"Transfer blocked by DLP policy: {dlp_decision.matched_rule_name}"
            )

        encryption_result = self._encryption_engine.encrypt_file(
            input_path=file_path,
            output_dir=output_dir,
            actor=actor,
        )

        token = secrets.token_urlsafe(24)
        expires_at_dt = datetime.utcnow() + timedelta(hours=max(1, expires_in_hours))
        expires_at = expires_at_dt.strftime("%Y-%m-%d %H:%M:%S")
        share_id = self._share_repository.create_share(
            share_token=token,
            file_id=encryption_result.file_id,
            recipient_id=recipient.recipient_id,
            created_by=actor,
            expires_at=expires_at,
        )
        share_link = f"localshare://sft-dlp/{token}?exp={expires_at}"

        self._audit_service.log(
            event_type="share_created",
            actor=actor,
            status="success",
            message="Encrypted share link generated.",
            file_id=encryption_result.file_id,
            recipient_id=recipient.recipient_id,
            share_id=share_id,
            metadata={
                "share_link": share_link,
                "encrypted_file": str(encryption_result.encrypted_path),
                "expires_at": expires_at,
            },
        )

        return ShareResult(
            share_id=share_id,
            share_link=share_link,
            expires_at=expires_at,
            file_id=encryption_result.file_id,
        )
