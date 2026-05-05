from __future__ import annotations

import sqlite3
from pathlib import Path


class DatabaseConnectionFactory:
    """Creates SQLite connections with consistent safety settings."""

    def __init__(self, db_path: Path) -> None:
        """Store SQLite path and ensure parent directory exists.

        Args:
            db_path: SQLite database file path.

        Returns:
            None.
        """
        self._db_path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        """Create a SQLite connection with foreign-key support enabled.

        Args:
            None.

        Returns:
            Configured SQLite connection.
        """
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn
