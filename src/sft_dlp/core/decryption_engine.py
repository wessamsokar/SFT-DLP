from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from Crypto.Cipher import AES

from sft_dlp.config import BASE_DIR
from sft_dlp.core.audit_service import AuditService
from sft_dlp.core.encryption_engine import MAGIC_HEADER, NONCE_SIZE, TAG_SIZE
from sft_dlp.core.key_manager import OpenSSLKeyManager
from sft_dlp.db.repositories import FileRepository
from sft_dlp.utils.file_utils import validate_path_within_base


@dataclass
class DecryptionResult:
    """Result payload returned after successful decryption.

    Attributes:
        file_id: Database id for encrypted file metadata.
        decrypted_path: Path of generated plaintext file.
    """

    file_id: int
    decrypted_path: Path


class FileDecryptionEngine:
    """Decrypts locally encrypted files for authorized share access."""

    def __init__(
        self,
        file_repository: FileRepository,
        key_manager: OpenSSLKeyManager,
        audit_service: AuditService,
    ) -> None:
        self._file_repository = file_repository
        self._key_manager = key_manager
        self._audit_service = audit_service

    def decrypt_file(
        self,
        *,
        file_id: int,
        output_dir: Path,
        actor: str,
    ) -> DecryptionResult:
        """Decrypt an encrypted payload for an authorized access request.

        Args:
            file_id: Database identifier of encrypted file.
            output_dir: Directory where plaintext should be written.
            actor: User identifier used in audit logs.

        Returns:
            Decryption result containing file id and plaintext output path.
        """
        encrypted_path: Path | None = None
        key_id: str | None = None

        try:
            file_record = self._file_repository.get_file_by_id(file_id)
            if not file_record:
                raise FileNotFoundError(f"File metadata not found for file_id={file_id}")

            encrypted_path = file_record.encrypted_path.resolve()
            if not encrypted_path.exists() or not encrypted_path.is_file():
                raise FileNotFoundError(f"Encrypted file not found: {encrypted_path}")

            key_record = self._key_manager.get_key_by_id(file_record.encryption_key_id)
            if not key_record:
                raise KeyError(f"Encryption key not found for key_id={file_record.encryption_key_id}")
            key_id = key_record.key_id
            key_bytes = self._key_manager.load_key_bytes(key_record)

            payload = encrypted_path.read_bytes()
            header_len = len(MAGIC_HEADER)
            if len(payload) < header_len + NONCE_SIZE + TAG_SIZE:
                raise ValueError("Encrypted payload is too short or malformed.")

            header = payload[:header_len]
            if header != MAGIC_HEADER:
                raise ValueError("Invalid encrypted file header.")

            offset = header_len
            nonce = payload[offset : offset + NONCE_SIZE]
            offset += NONCE_SIZE
            tag = payload[offset : offset + TAG_SIZE]
            offset += TAG_SIZE
            ciphertext = payload[offset:]

            cipher = AES.new(key_bytes, AES.MODE_GCM, nonce=nonce)
            plaintext = cipher.decrypt_and_verify(ciphertext, tag)

            output_dir = validate_path_within_base(output_dir, base_dir=BASE_DIR)
            output_dir.mkdir(parents=True, exist_ok=True)
            decrypted_path = output_dir / f"{file_record.original_name}.decrypted"
            decrypted_path.write_bytes(plaintext)

            self._audit_service.log(
                event_type="file_decrypted",
                actor=actor,
                status="success",
                message=f"Decrypted file_id={file_id} to {decrypted_path.name}",
                file_id=file_id,
                metadata={"output_path": str(decrypted_path)},
            )

            return DecryptionResult(file_id=file_id, decrypted_path=decrypted_path)
        except Exception as exc:
            self._audit_service.log(
                event_type="file_decryption_failed",
                actor=actor,
                status="error",
                message=f"Decryption failed for file_id={file_id}: {exc}",
                file_id=file_id,
                metadata={
                    "encrypted_path": str(encrypted_path) if encrypted_path else None,
                    "key_id": key_id,
                },
            )
            raise
