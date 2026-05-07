# Secure File Transfer & Data Leakage Prevention System (SFT-DLP)

SFT-DLP is a local-first desktop application that secures file transfer through strong encryption, DLP policy enforcement, and auditable sharing workflows. It helps prevent accidental or unauthorized data leakage by scanning transfer candidates before sharing and blocking risky content. The system combines cryptography, policy controls, and monitoring in one PyQt5 interface for practical secure collaboration.

## Features

- AES-256-GCM file encryption and authenticated decryption.
- PBKDF2-HMAC-SHA256 key derivation for encryption key material (600,000 iterations).
- Configurable DLP policy engine:
  - regex pattern detection (e.g., IDs, credit-card-like content),
  - file type blocking,
  - recipient authorization controls.
- Secure local sharing links with token generation and expiration enforcement.
- End-to-end audit logging in SQLite for encryption, DLP, sharing, and access attempts.
- PyQt5 desktop GUI with tabs for Encryption, Sharing, DLP Rules, and Audit Logs.
- Path traversal protection for user-supplied file/folder paths.

## Requirements

- Python 3.10 or newer.
- OpenSSL CLI installed and available via `OPENSSL_BIN` or system `PATH`.
- Operating systems:
  - Windows 10/11 (primary tested environment),
  - Linux/macOS (expected compatible with Python + PyQt5 + OpenSSL available).

## Installation & Setup

1. Clone the repository:

```bash
git clone https://github.com/wessamsokar/SFT-DLP.git
cd SFT-DLP
```

2. Create a virtual environment:

```bash
python -m venv .venv
```

3. Activate the virtual environment:

- Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

- Linux/macOS:

```bash
source .venv/bin/activate
```

4. Install dependencies:

```bash
pip install -r requirements.txt
```

5. Initialize the SQLite database:

```bash
python scripts/init_db.py --force-reset
```

This creates `data/sft_dlp.db` and seeds default DLP rules.

## How to Run

From project root:

```bash
python scripts/run_app.py
```

Alternative module run:

```bash
python -m sft_dlp.main
```

## Usage Examples

### Encrypt a File

1. Open the **Encryption** tab.
2. Choose an input file and encrypted output directory.
3. Click **Encrypt File (AES-256-GCM)**.
4. Confirm success message and generated `.sftenc` file.

[Screenshot: encryption tab]

### Share a File Securely

1. Open the **Sharing** tab.
2. Select source file, recipient details, and expiration hours.
3. Click **Create Secure Share Link**.
4. If DLP rules are triggered, sharing is blocked with an error message.
5. Copy/use the generated local share link or token.


### View Audit Logs

1. Open the **Audit Logs** tab.
2. Click **Refresh Logs**.
3. Review event records with status badges (Success, Blocked, Expired, Error).

[Screenshot: audit logs tab]

## Project Structure

```text
SFT-DLP/
├── data/                      # Runtime files (DB, encrypted/decrypted samples)
├── keys/                      # Local key files used by the key manager
├── logs/                      # Optional runtime log outputs
├── scripts/
│   ├── init_db.py             # CLI entrypoint to initialize/reset SQLite schema
│   └── run_app.py             # CLI entrypoint to run the desktop app
├── src/sft_dlp/
│   ├── config.py              # Global paths and app constants
│   ├── main.py                # App composition and dependency wiring
│   ├── core/
│   │   ├── encryption_engine.py   # AES-256-GCM encryption workflow
│   │   ├── decryption_engine.py   # AES-256-GCM decryption workflow
│   │   ├── key_manager.py         # OpenSSL integration and PBKDF2-based key derivation
│   │   ├── dlp_engine.py          # DLP rule evaluation logic
│   │   ├── sharing_service.py     # DLP-guarded secure link creation
│   │   ├── share_access_service.py# Token validation + expiry-enforced file access
│   │   └── audit_service.py       # High-level audit log writing
│   ├── db/
│   │   ├── schema.sql          # SQLite schema definition
│   │   ├── connection.py       # DB connection factory
│   │   ├── init_db.py          # Schema initialization + default rule seeding
│   │   └── repositories.py     # Data access layer (parameterized SQL)
│   ├── gui/
│   │   ├── main_window.py      # Main window + navigation layout
│   │   ├── theme.py            # Global QSS UI theme
│   │   └── tabs/               # Feature-specific GUI tabs
│   └── utils/
│       └── file_utils.py       # Hashing, MIME, and secure path validation helpers
├── requirements.txt            # Python dependencies
└── README.md                   # Project documentation
```

## Security Notes

- Encryption uses **AES-256-GCM** with random nonce generation per file and authentication tag verification.
- Key material is derived with **PBKDF2-HMAC-SHA256** using a random salt and **600,000 iterations**.
- **DLP checks are enforced before sharing**; blocked policies stop transfer and log the event.
- Share access enforces **link expiration** at access time and denies expired tokens.
- File path inputs are validated using absolute-path checks and base-directory boundary enforcement to mitigate path traversal.
