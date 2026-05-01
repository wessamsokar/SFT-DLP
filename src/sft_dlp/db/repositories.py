from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .connection import DatabaseConnectionFactory


@dataclass
class KeyRecord:
    key_id: str
    key_path: Path


@dataclass
class RecipientRecord:
    recipient_id: int
    name: str
    email: str
    is_authorized: bool


@dataclass
class DlpRuleRecord:
    rule_id: int
    rule_name: str
    rule_type: str
    match_expression: str
    action: str
    severity: str
    enabled: bool


@dataclass
class FileRecord:
    file_id: int
    original_name: str
    encrypted_path: Path
    encryption_key_id: str


@dataclass
class ShareRecord:
    share_id: int
    share_token: str
    file_id: int
    recipient_id: int | None
    expires_at: str
    revoked_at: str | None


class AuditLogRepository:
    def __init__(self, connection_factory: DatabaseConnectionFactory) -> None:
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
    def __init__(self, connection_factory: DatabaseConnectionFactory) -> None:
        self._connection_factory = connection_factory

    def get_active_key(self) -> KeyRecord | None:
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
    def __init__(self, connection_factory: DatabaseConnectionFactory) -> None:
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
    def __init__(self, connection_factory: DatabaseConnectionFactory) -> None:
        self._connection_factory = connection_factory

    def upsert_recipient(self, *, name: str, email: str, is_authorized: bool) -> RecipientRecord:
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
    def __init__(self, connection_factory: DatabaseConnectionFactory) -> None:
        self._connection_factory = connection_factory

    def get_enabled_rules(self) -> list[DlpRuleRecord]:
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
        with self._connection_factory.connect() as conn:
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


class DlpEventRepository:
    def __init__(self, connection_factory: DatabaseConnectionFactory) -> None:
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
    def __init__(self, connection_factory: DatabaseConnectionFactory) -> None:
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
