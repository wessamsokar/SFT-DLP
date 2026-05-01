PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS app_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    role TEXT NOT NULL DEFAULT 'operator',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS recipients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    is_authorized INTEGER NOT NULL DEFAULT 0 CHECK (is_authorized IN (0, 1)),
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS key_store (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key_id TEXT NOT NULL UNIQUE,
    key_label TEXT NOT NULL,
    key_path TEXT NOT NULL,
    fingerprint TEXT,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    rotated_at TEXT
);

CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_path TEXT NOT NULL,
    original_name TEXT NOT NULL,
    mime_type TEXT,
    file_size_bytes INTEGER,
    file_sha256 TEXT,
    encrypted_path TEXT,
    encryption_key_id TEXT,
    nonce_b64 TEXT,
    tag_b64 TEXT,
    status TEXT NOT NULL DEFAULT 'staged',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT,
    FOREIGN KEY (encryption_key_id) REFERENCES key_store(key_id)
);

CREATE TABLE IF NOT EXISTS dlp_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_name TEXT NOT NULL UNIQUE,
    rule_type TEXT NOT NULL CHECK (rule_type IN ('pattern', 'file_type', 'recipient')),
    match_expression TEXT NOT NULL,
    action TEXT NOT NULL DEFAULT 'block' CHECK (action IN ('allow', 'warn', 'block')),
    severity TEXT NOT NULL DEFAULT 'high' CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    enabled INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS dlp_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER,
    recipient_id INTEGER,
    rule_id INTEGER,
    matched_text TEXT,
    decision TEXT NOT NULL CHECK (decision IN ('allow', 'warn', 'block')),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (file_id) REFERENCES files(id),
    FOREIGN KEY (recipient_id) REFERENCES recipients(id),
    FOREIGN KEY (rule_id) REFERENCES dlp_rules(id)
);

CREATE TABLE IF NOT EXISTS shares (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    share_token TEXT NOT NULL UNIQUE,
    file_id INTEGER NOT NULL,
    recipient_id INTEGER,
    created_by TEXT,
    expires_at TEXT NOT NULL,
    revoked_at TEXT,
    last_accessed_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT,
    FOREIGN KEY (file_id) REFERENCES files(id),
    FOREIGN KEY (recipient_id) REFERENCES recipients(id)
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    actor TEXT NOT NULL,
    file_id INTEGER,
    recipient_id INTEGER,
    share_id INTEGER,
    status TEXT NOT NULL CHECK (status IN ('success', 'warning', 'blocked', 'error')),
    message TEXT NOT NULL,
    metadata_json TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (file_id) REFERENCES files(id),
    FOREIGN KEY (recipient_id) REFERENCES recipients(id),
    FOREIGN KEY (share_id) REFERENCES shares(id)
);

CREATE INDEX IF NOT EXISTS idx_files_created_at ON files(created_at);
CREATE INDEX IF NOT EXISTS idx_dlp_events_created_at ON dlp_events(created_at);
CREATE INDEX IF NOT EXISTS idx_shares_expires_at ON shares(expires_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_event_type ON audit_logs(event_type);
