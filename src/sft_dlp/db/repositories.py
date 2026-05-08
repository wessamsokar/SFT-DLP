from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .connection import DatabaseConnectionFactory


@dataclass
class KeyRecord:
    """Key metadata tuple used by encryption services."""

    key_id: str
    key_path: Path


@dataclass
class RecipientRecord:
    """Recipient metadata tuple used by sharing/DLP services."""

    recipient_id: int
    name: str
    email: str
    is_authorized: bool


@dataclass
class DlpRuleRecord:
    """Active DLP rule tuple loaded from persistence."""

    rule_id: int
    rule_name: str
    rule_type: str
    match_expression: str
    action: str
    severity: str
    enabled: bool


@dataclass
class FileRecord:
    """Encrypted file metadata tuple loaded from persistence."""

    file_id: int
    original_name: str
    encrypted_path: Path
    encryption_key_id: str


@dataclass
class ShareRecord:
    """Share metadata tuple loaded from persistence."""

    share_id: int
    share_token: str
    file_id: int
    recipient_id: int | None
    expires_at: str
    revoked_at: str | None


class AuditLogRepository:
    """Persistence operations for audit log records."""

    def __init__(self, connection_factory: DatabaseConnectionFactory) -> None:
        """Initialize repository with DB connection factory.

        Args:
            connection_factory: SQLite connection provider.

        Returns:
            None.
        """
        self._connection_factory = connection_factory

    def log_event(
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
        """Insert a new audit event row.

        Args:
            event_type: Normalized event identifier.
            actor: User or service actor.
            status: Event status value.
            message: Human-readable event description.
            file_id: Optional file id.
            recipient_id: Optional recipient id.
            share_id: Optional share id.
            metadata: Optional metadata payload.

        Returns:
            None.
        """
        metadata_json = json.dumps(metadata or {})
        with self._connection_factory.connect() as conn:
            conn.execute(
                """
                INSERT INTO audit_logs (
                    event_type, actor, file_id, recipient_id, share_id, status, message, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_type,
                    actor,
                    file_id,
                    recipient_id,
                    share_id,
                    status,
                    message,
                    metadata_json,
                ),
            )
            conn.commit()

    def get_recent_logs(self, limit: int = 200) -> list[dict[str, Any]]:
        """Fetch recent audit logs sorted newest-first.

        Args:
            limit: Maximum number of rows.

        Returns:
            List of row dictionaries.
        """
        with self._connection_factory.connect() as conn:
            rows = conn.execute(
                """
                SELECT id, event_type, actor, status, message, created_at
                FROM audit_logs
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]


class KeyStoreRepository:
    """Persistence operations for encryption key metadata."""

    def __init__(self, connection_factory: DatabaseConnectionFactory) -> None:
        """Initialize key store repository.

        Args:
            connection_factory: SQLite connection provider.

        Returns:
            None.
        """
        self._connection_factory = connection_factory

    def get_active_key(self) -> KeyRecord | None:
        """Return most recent active key record.

        Args:
            None.

        Returns:
            Active key record or None.
        """
        with self._connection_factory.connect() as conn:
            row = conn.execute(
                """
                SELECT key_id, key_path
                FROM key_store
                WHERE is_active = 1
                ORDER BY created_at DESC, id DESC
                LIMIT 1
                """
            ).fetchone()
        if not row:
            return None
        return KeyRecord(key_id=row["key_id"], key_path=Path(row["key_path"]))

    def get_key_by_id(self, key_id: str) -> KeyRecord | None:
        """Return key record by key id.

        Args:
            key_id: Unique key identifier.

        Returns:
            Matching key record or None.
        """
        with self._connection_factory.connect() as conn:
            row = conn.execute(
                """
                SELECT key_id, key_path
                FROM key_store
                WHERE key_id = ?
                LIMIT 1
                """,
                (key_id,),
            ).fetchone()
        if not row:
            return None
        return KeyRecord(key_id=row["key_id"], key_path=Path(row["key_path"]))

    def insert_key(
        self,
        *,
        key_id: str,
        key_label: str,
        key_path: Path,
        fingerprint: str,
        is_active: bool,
    ) -> None:
        """Insert new key metadata and optionally rotate previous active key.

        Args:
            key_id: Generated key identifier.
            key_label: Human-readable key label.
            key_path: Filesystem path of key bytes.
            fingerprint: SHA-256 fingerprint.
            is_active: Whether key should be active.

        Returns:
            None.
        """
        with self._connection_factory.connect() as conn:
            if is_active:
                conn.execute("UPDATE key_store SET is_active = 0, rotated_at = datetime('now') WHERE is_active = 1")
            conn.execute(
                """
                INSERT INTO key_store (key_id, key_label, key_path, fingerprint, is_active)
                VALUES (?, ?, ?, ?, ?)
                """,
                (key_id, key_label, str(key_path), fingerprint, 1 if is_active else 0),
            )
            conn.commit()


class FileRepository:
    """Persistence operations for encrypted file metadata."""

    def __init__(self, connection_factory: DatabaseConnectionFactory) -> None:
        """Initialize file repository.

        Args:
            connection_factory: SQLite connection provider.

        Returns:
            None.
        """
        self._connection_factory = connection_factory

    def insert_encrypted_file(
        self,
        *,
        original_path: Path,
        mime_type: str,
        file_size_bytes: int,
        file_sha256: str,
        encrypted_path: Path,
        encryption_key_id: str,
        nonce_b64: str,
        tag_b64: str,
        status: str,
    ) -> int:
        """Insert encrypted file metadata row.

        Args:
            original_path: Original source path.
            mime_type: MIME type string.
            file_size_bytes: Original file size.
            file_sha256: SHA-256 hash of plaintext.
            encrypted_path: Encrypted payload path.
            encryption_key_id: Key id used for encryption.
            nonce_b64: Base64-encoded GCM nonce.
            tag_b64: Base64-encoded GCM authentication tag.
            status: File processing status.

        Returns:
            Inserted file row id.
        """
        with self._connection_factory.connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO files (
                    original_path,
                    original_name,
                    mime_type,
                    file_size_bytes,
                    file_sha256,
                    encrypted_path,
                    encryption_key_id,
                    nonce_b64,
                    tag_b64,
                    status,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                """,
                (
                    str(original_path),
                    original_path.name,
                    mime_type,
                    file_size_bytes,
                    file_sha256,
                    str(encrypted_path),
                    encryption_key_id,
                    nonce_b64,
                    tag_b64,
                    status,
                ),
            )
            conn.commit()
            return int(cursor.lastrowid)

    def get_file_by_id(self, file_id: int) -> FileRecord | None:
        """Fetch file metadata by id.

        Args:
            file_id: File identifier.

        Returns:
            File record or None.
        """
        with self._connection_factory.connect() as conn:
            row = conn.execute(
                """
                SELECT id, original_name, encrypted_path, encryption_key_id
                FROM files
                WHERE id = ?
                LIMIT 1
                """,
                (file_id,),
            ).fetchone()
        if not row:
            return None
        return FileRecord(
            file_id=int(row["id"]),
            original_name=str(row["original_name"]),
            encrypted_path=Path(row["encrypted_path"]),
            encryption_key_id=str(row["encryption_key_id"]),
        )


class RecipientRepository:
    """Persistence operations for share recipients."""

    def __init__(self, connection_factory: DatabaseConnectionFactory) -> None:
        """Initialize recipient repository.

        Args:
            connection_factory: SQLite connection provider.

        Returns:
            None.
        """
        self._connection_factory = connection_factory

    def upsert_recipient(self, *, name: str, email: str, is_authorized: bool) -> RecipientRecord:
        """Insert or update recipient by email.

        Args:
            name: Recipient display name.
            email: Recipient email address.
            is_authorized: Recipient authorization flag.

        Returns:
            Upserted recipient record.
        """
        normalized_email = email.strip().lower()
        normalized_name = name.strip() or normalized_email
        with self._connection_factory.connect() as conn:
            conn.execute(
                """
                INSERT INTO recipients (name, email, is_authorized, updated_at)
                VALUES (?, ?, ?, datetime('now'))
                ON CONFLICT(email) DO UPDATE SET
                    name = excluded.name,
                    is_authorized = excluded.is_authorized,
                    updated_at = datetime('now')
                """,
                (normalized_name, normalized_email, 1 if is_authorized else 0),
            )
            row = conn.execute(
                """
                SELECT id, name, email, is_authorized
                FROM recipients
                WHERE email = ?
                """,
                (normalized_email,),
            ).fetchone()
            conn.commit()
        return RecipientRecord(
            recipient_id=int(row["id"]),
            name=str(row["name"]),
            email=str(row["email"]),
            is_authorized=bool(row["is_authorized"]),
        )

    def get_by_email(self, email: str) -> RecipientRecord | None:
        """Get recipient by normalized email.

        Args:
            email: Recipient email address.

        Returns:
            Recipient record or None.
        """
        normalized_email = email.strip().lower()
        with self._connection_factory.connect() as conn:
            row = conn.execute(
                """
                SELECT id, name, email, is_authorized
                FROM recipients
                WHERE email = ?
                """,
                (normalized_email,),
            ).fetchone()
        if not row:
            return None
        return RecipientRecord(
            recipient_id=int(row["id"]),
            name=str(row["name"]),
            email=str(row["email"]),
            is_authorized=bool(row["is_authorized"]),
        )


class DlpRuleRepository:
    """Persistence operations for DLP rule management."""

    def __init__(self, connection_factory: DatabaseConnectionFactory) -> None:
        """Initialize DLP rule repository.

        Args:
            connection_factory: SQLite connection provider.

        Returns:
            None.
        """
        self._connection_factory = connection_factory

    def get_enabled_rules(self) -> list[DlpRuleRecord]:
        """Load all enabled DLP rules in insertion order.

        Args:
            None.

        Returns:
            List of enabled DLP rule records.
        """
        with self._connection_factory.connect() as conn:
            rows = conn.execute(
                """
                SELECT id, rule_name, rule_type, match_expression, action, severity, enabled
                FROM dlp_rules
                WHERE enabled = 1
                ORDER BY id ASC
                """
            ).fetchall()
        return [
            DlpRuleRecord(
                rule_id=int(row["id"]),
                rule_name=str(row["rule_name"]),
                rule_type=str(row["rule_type"]),
                match_expression=str(row["match_expression"]),
                action=str(row["action"]),
                severity=str(row["severity"]),
                enabled=bool(row["enabled"]),
            )
            for row in rows
        ]

    def create_rule(
        self,
        *,
        rule_name: str,
        rule_type: str,
        match_expression: str,
        action: str,
        severity: str,
        enabled: bool,
    ) -> None:
        """Create a new DLP rule.

        Args:
            rule_name: Unique rule name.
            rule_type: Rule kind (`pattern`, `file_type`, `recipient`).
            match_expression: Rule match expression.
            action: Rule action (`allow`, `warn`, `block`).
            severity: Rule severity.
            enabled: Whether rule is active.

        Returns:
            None.
        """
        with self._connection_factory.connect() as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO dlp_rules (
                        rule_name,
                        rule_type,
                        match_expression,
                        action,
                        severity,
                        enabled,
                        updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
                    """,
                    (
                        rule_name,
                        rule_type,
                        match_expression,
                        action,
                        severity,
                        1 if enabled else 0,
                    ),
                )
                conn.commit()
            except sqlite3.IntegrityError as exc:
                if "dlp_rules.rule_name" in str(exc):
                    raise ValueError(f"A DLP rule named '{rule_name}' already exists.") from exc
                raise

    def delete_rule(self, rule_id: int) -> bool:
        """Delete a DLP rule by id and remove dependent DLP events.

        Args:
            rule_id: Rule identifier to remove.

        Returns:
            True when a rule row is deleted, False when no row matches.
        """
        with self._connection_factory.connect() as conn:
            # Remove dependent history rows first to satisfy FK constraints.
            conn.execute("DELETE FROM dlp_events WHERE rule_id = ?", (rule_id,))
            cursor = conn.execute("DELETE FROM dlp_rules WHERE id = ?", (rule_id,))
            conn.commit()
            return cursor.rowcount > 0


class DlpEventRepository:
    """Persistence operations for DLP evaluation events."""

    def __init__(self, connection_factory: DatabaseConnectionFactory) -> None:
        """Initialize DLP event repository.

        Args:
            connection_factory: SQLite connection provider.

        Returns:
            None.
        """
        self._connection_factory = connection_factory

    def record_event(
        self,
        *,
        file_id: int | None,
        recipient_id: int | None,
        rule_id: int,
        matched_text: str,
        decision: str,
    ) -> None:
        """Insert DLP rule hit event.

        Args:
            file_id: Optional related file id.
            recipient_id: Optional related recipient id.
            rule_id: Matched rule id.
            matched_text: Matched excerpt.
            decision: Rule decision.

        Returns:
            None.
        """
        with self._connection_factory.connect() as conn:
            conn.execute(
                """
                INSERT INTO dlp_events (file_id, recipient_id, rule_id, matched_text, decision)
                VALUES (?, ?, ?, ?, ?)
                """,
                (file_id, recipient_id, rule_id, matched_text, decision),
            )
            conn.commit()


class ShareRepository:
    """Persistence operations for secure share links."""

    def __init__(self, connection_factory: DatabaseConnectionFactory) -> None:
        """Initialize share repository.

        Args:
            connection_factory: SQLite connection provider.

        Returns:
            None.
        """
        self._connection_factory = connection_factory

    def create_share(
        self,
        *,
        share_token: str,
        file_id: int,
        recipient_id: int | None,
        created_by: str,
        expires_at: str,
    ) -> int:
        """Insert new share record.

        Args:
            share_token: Random share token.
            file_id: Related encrypted file id.
            recipient_id: Optional recipient id.
            created_by: Actor creating the share.
            expires_at: Expiration timestamp string.

        Returns:
            Inserted share id.
        """
        with self._connection_factory.connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO shares (share_token, file_id, recipient_id, created_by, expires_at, updated_at)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
                """,
                (share_token, file_id, recipient_id, created_by, expires_at),
            )
            conn.commit()
            return int(cursor.lastrowid)

    def get_by_token(self, share_token: str) -> ShareRecord | None:
        """Fetch share record by token.

        Args:
            share_token: Share token value.

        Returns:
            Share record or None.
        """
        with self._connection_factory.connect() as conn:
            row = conn.execute(
                """
                SELECT id, share_token, file_id, recipient_id, expires_at, revoked_at
                FROM shares
                WHERE share_token = ?
                LIMIT 1
                """,
                (share_token,),
            ).fetchone()
        if not row:
            return None
        return ShareRecord(
            share_id=int(row["id"]),
            share_token=str(row["share_token"]),
            file_id=int(row["file_id"]),
            recipient_id=int(row["recipient_id"]) if row["recipient_id"] is not None else None,
            expires_at=str(row["expires_at"]),
            revoked_at=str(row["revoked_at"]) if row["revoked_at"] is not None else None,
        )

    def mark_accessed(self, share_id: int) -> None:
        """Update share access timestamp.

        Args:
            share_id: Share identifier.

        Returns:
            None.
        """
        with self._connection_factory.connect() as conn:
            conn.execute(
                """
                UPDATE shares
                SET last_accessed_at = datetime('now'), updated_at = datetime('now')
                WHERE id = ?
                """,
                (share_id,),
            )
            conn.commit()
