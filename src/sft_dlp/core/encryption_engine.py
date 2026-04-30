from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

from sft_dlp.core.audit_service import AuditService
from sft_dlp.core.key_manager import OpenSSLKeyManager
from sft_dlp.db.repositories import FileRepository
from sft_dlp.utils.file_utils import compute_file_sha256, guess_mime_type

MAGIC_HEADER = b"SFTDLP1"
NONCE_SIZE = 12
TAG_SIZE = 16


@dataclass
class EncryptionResult:
    file_id: int
    encrypted_path: Path
    key_id: str


class FileEncryptionEngine:
    """Encrypts files locally with AES-256-GCM before transfer."""

    def __init__(
        self,
        file_repository: FileRepository,
        key_manager: OpenSSLKeyManager,
        audit_service: AuditService,
    ) -> None:
        self._file_repository = file_repository
        self._key_manager = key_manager
        self._audit_service = audit_service

    def encrypt_file(
        self,
        input_path: Path,
        output_dir: Path,
        actor: str = "operator",
    ) -> EncryptionResult:
        input_path = input_path.resolve()
        output_dir = output_dir.resolve()
        key_id: str | None = None
        encrypted_path: Path | None = None

        try:
            output_dir.mkdir(parents=True, exist_ok=True)

            if not input_path.exists() or not input_path.is_file():
                raise FileNotFoundError(f"Input file not found: {input_path}")

            key_record = self._key_manager.get_or_create_active_key()
            key_id = key_record.key_id
            key_bytes = self._key_manager.load_key_bytes(key_record)

            plaintext = input_path.read_bytes()
            nonce = get_random_bytes(NONCE_SIZE)
            cipher = AES.new(key_bytes, AES.MODE_GCM, nonce=nonce)
            ciphertext, tag = cipher.encrypt_and_digest(plaintext)

            encrypted_path = output_dir / f"{input_path.name}.sftenc"
            payload = MAGIC_HEADER + nonce + tag + ciphertext
            encrypted_path.write_bytes(payload)

            mime_type = guess_mime_type(input_path)
            sha256_hex = compute_file_sha256(input_path)
            file_id = self._file_repository.insert_encrypted_file(
                original_path=input_path,
                mime_type=mime_type,
                file_size_bytes=input_path.stat().st_size,
                file_sha256=sha256_hex,
                encrypted_path=encrypted_path,
                encryption_key_id=key_record.key_id,
                nonce_b64=base64.b64encode(nonce).decode("ascii"),
                tag_b64=base64.b64encode(tag).decode("ascii"),
                status="encrypted",
            )

            self._audit_service.log(
                event_type="file_encrypted",
                actor=actor,
                status="success",
                message=f"Encrypted {input_path.name} to {encrypted_path.name}",
                file_id=file_id,
                metadata={
                    "algorithm": "AES-256-GCM",
                    "key_id": key_record.key_id,
                    "output_path": str(encrypted_path),
                },
            )

            return EncryptionResult(
                file_id=file_id,
                encrypted_path=encrypted_path,
                key_id=key_record.key_id,
            )
        except Exception as exc:
            self._audit_service.log(
                event_type="file_encryption_failed",
                actor=actor,
                status="error",
                message=f"Encryption failed for {input_path.name}: {exc}",
                metadata={
                    "input_path": str(input_path),
                    "output_dir": str(output_dir),
                    "key_id": key_id,
                    "encrypted_path": str(encrypted_path) if encrypted_path else None,
                },
            )
            raise
