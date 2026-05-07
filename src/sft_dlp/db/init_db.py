from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path("data") / "sft_dlp.db"
SCHEMA_PATH = Path(__file__).with_name("schema.sql")

DEFAULT_DLP_RULES = [
    (
        "National ID (generic)",
        "pattern",
        r"\b\d{3}-\d{2}-\d{4}\b",
        "block",
        "critical",
        1,
    ),
    (
        "Credit Card Number",
        "pattern",
        r"\b(?:\d[ -]*?){13,16}\b",
        "block",
        "critical",
        1,
    ),
    (
        "Private Key Files",
        "file_type",
        ".pem,.key,.p12,.pfx",
        "block",
        "high",
        1,
    ),
    (
        "Unapproved Recipient",
        "recipient",
        "is_authorized=0",
        "block",
        "high",
        1,
    ),
]


def _resolve_db_path(raw_db_path: str | None) -> Path:
    """Resolve custom DB argument to concrete path.

    Args:
        raw_db_path: Optional user-supplied DB path.

    Returns:
        Resolved database path.
    """
    if not raw_db_path:
        return DEFAULT_DB_PATH
    return Path(raw_db_path)


def initialize_database(db_path: str | None = None, force_reset: bool = False) -> Path:
    """Create and initialize the SQLite database with required schema and seed data."""
    resolved_db_path = _resolve_db_path(db_path)
    resolved_db_path.parent.mkdir(parents=True, exist_ok=True)

    if force_reset and resolved_db_path.exists():
        resolved_db_path.unlink()

    with sqlite3.connect(resolved_db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
        conn.executescript(schema_sql)
        conn.executemany(
            """
            INSERT OR IGNORE INTO dlp_rules
            (rule_name, rule_type, match_expression, action, severity, enabled)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            DEFAULT_DLP_RULES,
        )
        conn.execute(
            """
            INSERT INTO audit_logs (event_type, actor, status, message, metadata_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "database_initialized",
                "system",
                "success",
                "Database schema initialized successfully.",
                '{"component": "db.init"}',
            ),
        )
        conn.commit()

    return resolved_db_path


def main() -> None:
    """CLI entry point for database initialization.

    Args:
        None.

    Returns:
        None.
    """
    parser = argparse.ArgumentParser(
        description="Initialize local SQLite database for SFT-DLP"
    )
    parser.add_argument(
        "--db-path",
        default=None,
        help="Optional custom SQLite database path (default: data/sft_dlp.db)",
    )
    parser.add_argument(
        "--force-reset",
        action="store_true",
        help="Delete existing DB file before initializing",
    )
    args = parser.parse_args()

    db_file = initialize_database(db_path=args.db_path, force_reset=args.force_reset)
    print(f"Database initialized at: {db_file}")


if __name__ == "__main__":
    main()
