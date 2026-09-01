import os
import sys
from pathlib import Path

# Application Metadata
APP_NAME = "StudySpace Manager"
APP_VERSION = "1.0.0 (Offline MVP)"
DEFAULT_LIBRARY_NAME = "Apex Study Library & Reading Hall"
DEFAULT_COOLDOWN_SECONDS = 60
DEFAULT_ATTENDANCE_MODE = "CHECKIN_CHECKOUT"  # Options: 'CHECKIN_CHECKOUT', 'DAILY_PRESENCE'
DEFAULT_CAMERA_INDEX = 0

# Base Application Directory (works in both dev mode and PyInstaller bundle)
if getattr(sys, 'frozen', False):
    # Running inside PyInstaller frozen bundle
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    # Running in normal Python environment
    BASE_DIR = Path(__file__).resolve().parent.parent

# Data Directory Determination
def get_data_dir() -> Path:
    # 1. Environment variable override (e.g. for testing or custom deploy)
    env_dir = os.environ.get("STUDY_SPACE_DATA_DIR")
    if env_dir:
        p = Path(env_dir).resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p

    # 2. Portable mode flag
    if (BASE_DIR / "portable.flag").exists():
        p = BASE_DIR / "data"
        p.mkdir(parents=True, exist_ok=True)
        return p

    # 3. Development mode (run from workspace source repo)
    dev_data = BASE_DIR / "data"
    dev_data.mkdir(parents=True, exist_ok=True)
    return dev_data

DATA_DIR = get_data_dir()
BACKUP_DIR = DATA_DIR / "backups"
QR_DIR = DATA_DIR / "qr_cards"
EXPORTS_DIR = DATA_DIR / "exports"

BACKUP_DIR.mkdir(parents=True, exist_ok=True)
QR_DIR.mkdir(parents=True, exist_ok=True)
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Database Path
DB_PATH = DATA_DIR / "library_data.db"
