from pathlib import Path

# Main App Settings
APP_NAME = "Secure File Transfer & DLP Project"
BASE_DIR = Path(__file__).resolve().parents[2]

# Folders for the project
DATA_DIR = BASE_DIR / "data"
KEYS_DIR = BASE_DIR / "keys"
LOGS_DIR = BASE_DIR / "logs"

# Database file
DEFAULT_DB_PATH = DATA_DIR / "sft_dlp.db"
