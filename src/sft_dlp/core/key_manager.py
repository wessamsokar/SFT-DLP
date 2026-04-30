from __future__ import annotations

import shutil
import subprocess
import uuid
import os
from pathlib import Path

from sft_dlp.db.repositories import KeyRecord, KeyStoreRepository


class OpenSSLKeyManager:
    """Manages local AES keys using the OpenSSL CLI."""

    def __init__(
        self,
        key_store_repository: KeyStoreRepository,
        keys_dir: Path,
    ) -> None:
        self._key_store_repository = key_store_repository
        self._keys_dir = keys_dir
        self._keys_dir.mkdir(parents=True, exist_ok=True)

    def ensure_openssl_available(self) -> None:
        self._resolve_openssl_binary()

    def _resolve_openssl_binary(self) -> str:
        configured = os.environ.get("OPENSSL_BIN", "").strip()
        if configured and Path(configured).exists():
            return configured

        in_path = shutil.which("openssl")
        if in_path:
            return in_path

        windows_candidates = [
            Path("C:/Program Files/OpenSSL-Win64/bin/openssl.exe"),
            Path("C:/Program Files/OpenSSL-Win32/bin/openssl.exe"),
            Path("C:/OpenSSL-Win64/bin/openssl.exe"),
            Path("C:/OpenSSL-Win32/bin/openssl.exe"),
        ]
        for candidate in windows_candidates:
            if candidate.exists():
                return str(candidate)

        raise RuntimeError(
            "OpenSSL binary not found. Add OpenSSL to PATH or set OPENSSL_BIN to openssl.exe path."
        )

    def get_or_create_active_key(self, key_label: str = "active-master-key") -> KeyRecord:
        active = self._key_store_repository.get_active_key()
        if active and active.key_path.exists():
            return active
        return self.generate_new_active_key(key_label=key_label)

    def get_key_by_id(self, key_id: str) -> KeyRecord | None:
        return self._key_store_repository.get_key_by_id(key_id)

    def generate_new_active_key(self, key_label: str = "rotated-master-key") -> KeyRecord:
        openssl_bin = self._resolve_openssl_binary()

        key_id = uuid.uuid4().hex
        key_path = self._keys_dir / f"{key_id}.bin"

        self._run_command([openssl_bin, "rand", "-out", str(key_path), "32"])
        fingerprint = self._calculate_sha256_fingerprint(openssl_bin, key_path)

        self._key_store_repository.insert_key(
            key_id=key_id,
            key_label=key_label,
            key_path=key_path,
            fingerprint=fingerprint,
            is_active=True,
        )
        return KeyRecord(key_id=key_id, key_path=key_path)

    def load_key_bytes(self, key_record: KeyRecord) -> bytes:
        if not key_record.key_path.exists():
            raise FileNotFoundError(f"Key file does not exist: {key_record.key_path}")
        key_bytes = key_record.key_path.read_bytes()
        if len(key_bytes) != 32:
            raise ValueError("Invalid key length: expected 32 bytes for AES-256.")
        return key_bytes

    @staticmethod
    def _run_command(command: list[str]) -> str:
        try:
            completed = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
            )
            return completed.stdout.strip()
        except subprocess.CalledProcessError as exc:
            stderr = (exc.stderr or "").strip()
            raise RuntimeError(
                f"OpenSSL command failed: {' '.join(command)}. {stderr}"
            ) from exc

    def _calculate_sha256_fingerprint(self, openssl_bin: str, key_path: Path) -> str:
        output = self._run_command([openssl_bin, "dgst", "-sha256", str(key_path)])
        if "=" in output:
            return output.split("=")[-1].strip()
        return output.strip()
