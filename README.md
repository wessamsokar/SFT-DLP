# Secure File Transfer & Data Leakage Prevention System (SFT-DLP)

Local-first desktop application for secure file encryption, controlled sharing, DLP policy enforcement, and complete audit logging.

## Features

- Modern, responsive PyQt5 desktop UI with custom QSS theme and sidebar navigation (opens maximized).
- AES-256-GCM local encryption and decryption using PyCryptodome.
- OpenSSL-based key management with automatic fallback detection (OPENSSL_BIN, PATH, and common Windows locations).
- DLP policy engine with pattern, file type, and recipient authorization rules.
- Secure local share links with strict expiration enforcement and token validation.
- Comprehensive audit logging, including failed encryption/decryption attempts and invalid share tokens.
- Audit Logs UI includes status badges (Success, Blocked, Expired, Error).

## Project Structure

```
SFT-DLP/
├── data/
├── keys/
├── logs/
├── scripts/
│   └── init_db.py
├── src/
│   └── sft_dlp/
│       ├── config.py
│       ├── main.py
│       ├── core/
│       │   ├── audit_service.py
│       │   ├── dlp_engine.py
│       │   ├── encryption_engine.py
│       │   ├── key_manager.py
│       │   └── sharing_service.py
│       ├── db/
│       │   ├── connection.py
│       │   ├── init_db.py
│       │   ├── repositories.py
│       │   └── schema.sql
│       ├── gui/
│       │   ├── main_window.py
│       │   └── tabs/
│       │       ├── audit_logs_tab.py
│       │       ├── dlp_rules_tab.py
│       │       └── encryption_tab.py
│       │       └── sharing_tab.py
│       └── utils/
│           └── file_utils.py
├── requirements.txt
└── README.md
```

## Requirements

- Python 3.10+
- OpenSSL CLI available (auto-detected via OPENSSL_BIN, PATH, or common Windows install paths)
- Dependencies listed in requirements.txt (PyQt5, PyCryptodome)

## Setup

Install Python dependencies:

```powershell
py -3 -m pip install -r requirements.txt
```

Initialize/reset the local SQLite database:

```powershell
py -3 scripts/init_db.py --force-reset
```

This creates `data/sft_dlp.db` with all required tables.

OpenSSL detection:

- The key manager checks OPENSSL_BIN first, then PATH, then common Windows locations.
- If OpenSSL is not found, install it, add it to PATH, or set OPENSSL_BIN to the full path.

## Usage

Run the desktop app:

```powershell
py -3 -m sft_dlp.main
```

If needed, run from the source root:

```powershell
$env:PYTHONPATH = "src"
py -3 -m sft_dlp.main
```

App tabs overview:

- Encryption: Select a file and output folder to encrypt locally (AES-256-GCM).
- Sharing: Create secure share links with expiry and access shared files via token/link.
- DLP Rules: Add pattern, file type, or recipient rules; rules are enforced before sharing.
- Audit Logs: Review all events with status badges (Success, Blocked, Expired, Error), including failed encryption/decryption and invalid token attempts.

## Next Modules

- Recipient and policy administration improvements (edit/disable/delete)
- Search and filtering in audit logs
