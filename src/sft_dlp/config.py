from pathlib import Path

APP_NAME = "Secure File Transfer & Data Leakage Prevention System"
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
KEYS_DIR = BASE_DIR / "keys"
LOGS_DIR = BASE_DIR / "logs"
DEFAULT_DB_PATH = DATA_DIR / "sft_dlp.db"
