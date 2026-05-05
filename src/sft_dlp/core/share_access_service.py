from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from sft_dlp.config import BASE_DIR
from sft_dlp.core.audit_service import AuditService
from sft_dlp.core.decryption_engine import DecryptionResult, FileDecryptionEngine
from sft_dlp.db.repositories import ShareRepository
from sft_dlp.utils.file_utils import validate_path_within_base


@dataclass
class ShareAccessResult:
    """Result payload for successful share access.

    Attributes:
        share_id: Share record identifier.
        file_id: Related encrypted file identifier.
        decrypted_path: Path to decrypted plaintext output.
    """

    share_id: int
    file_id: int
    decrypted_path: Path


class ShareAccessService:
    """Validates share tokens and decrypts files when links are still valid."""

    def __init__(
        self,
        share_repository: ShareRepository,
        decryption_engine: FileDecryptionEngine,
        audit_service: AuditService,
    ) -> None:
        self._share_repository = share_repository
        self._decryption_engine = decryption_engine
        self._audit_service = audit_service

    def access_share(
        self,
        *,
        token_or_link: str,
        output_dir: Path,
        actor: str,
    ) -> ShareAccessResult:
        """Validate token/link, enforce expiration, and decrypt shared file.

        Args:
            token_or_link: Raw share token or URL-style share link.
            output_dir: Directory where decrypted content will be written.
            actor: User identifier used in audit logs.

        Returns:
            Share access result containing resolved file output.
        """
        output_dir = validate_path_within_base(output_dir, base_dir=BASE_DIR)
        token = self._extract_token(token_or_link)
        share_record = self._share_repository.get_by_token(token)
        if not share_record:
            token_prefix = token[:6] if token else ""
            self._audit_service.log(
                event_type="share_access_denied",
                actor=actor,
                status="blocked",
                message="Invalid share token.",
                metadata={"token_prefix": token_prefix},
            )
            raise PermissionError("Invalid share token.")

        if share_record.revoked_at is not None:
            self._audit_service.log(
                event_type="share_access_denied",
                actor=actor,
                status="blocked",
                message=f"Share {share_record.share_id} is revoked.",
                share_id=share_record.share_id,
                file_id=share_record.file_id,
            )
            raise PermissionError("Share link has been revoked.")

        expires_at = datetime.strptime(share_record.expires_at, "%Y-%m-%d %H:%M:%S")
        now_utc = datetime.utcnow()
        if now_utc > expires_at:
            self._audit_service.log(
                event_type="share_access_denied",
                actor=actor,
                status="blocked",
                message=f"Share {share_record.share_id} expired at {share_record.expires_at}.",
                share_id=share_record.share_id,
                file_id=share_record.file_id,
            )
            raise PermissionError("Share link has expired.")

        decryption_result: DecryptionResult = self._decryption_engine.decrypt_file(
            file_id=share_record.file_id,
            output_dir=output_dir,
            actor=actor,
        )
        self._share_repository.mark_accessed(share_record.share_id)

        self._audit_service.log(
            event_type="share_accessed",
            actor=actor,
            status="success",
            message=f"Share {share_record.share_id} accessed successfully.",
            file_id=share_record.file_id,
            share_id=share_record.share_id,
            metadata={"decrypted_path": str(decryption_result.decrypted_path)},
        )

        return ShareAccessResult(
            share_id=share_record.share_id,
            file_id=share_record.file_id,
            decrypted_path=decryption_result.decrypted_path,
        )

    @staticmethod
    def _extract_token(token_or_link: str) -> str:
        """Extract normalized token from plain text token or localshare link.

        Args:
            token_or_link: Input token or URL-like share link.

        Returns:
            Normalized token value without query parameters.
        """
        raw = token_or_link.strip()
        if "://" not in raw:
            return raw

        if "/" in raw:
            candidate = raw.rsplit("/", 1)[-1]
        else:
            candidate = raw

        if "?" in candidate:
            candidate = candidate.split("?", 1)[0]
        return candidate
