import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'
BACKUP_DIR = DATA_DIR / 'backups'
QR_DIR = DATA_DIR / 'qr_cards'

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
BACKUP_DIR.mkdir(exist_ok=True)
QR_DIR.mkdir(exist_ok=True)

# Database
DB_PATH = DATA_DIR / 'library_data.db'

# Defaults
DEFAULT_LIBRARY_NAME = 'Apex Study Library & Reading Hall'
DEFAULT_COOLDOWN_SECONDS = 60
DEFAULT_ATTENDANCE_MODE = 'CHECKIN_CHECKOUT'  # or 'DAILY_PRESENCE'
DEFAULT_CAMERA_INDEX = 0

APP_VERSION = '1.0.0 (Offline MVP)'
