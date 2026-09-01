import sqlite3
import shutil
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from core.config import DB_PATH, BACKUP_DIR
from core.database import get_connection

def create_database_backup(label: str = "manual") -> Path:
    """
    Perform a consistent SQLite online backup to BACKUP_DIR.
    Thread-safe and ACID compliant even during active writes.
    """
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y_%m_%d_%H%M%S")
    backup_filename = f"backup_{timestamp}_{label}.db"
    backup_filepath = BACKUP_DIR / backup_filename

    src_conn = get_connection()
    dst_conn = sqlite3.connect(backup_filepath)
    try:
        with dst_conn:
            src_conn.backup(dst_conn, pages=100)
    finally:
        dst_conn.close()
        src_conn.close()

    # Log in audit table
    conn = get_connection()
    try:
        cursor = conn.cursor()
        with conn:
            cursor.execute("""
                INSERT INTO audit_logs (action, entity_type, entity_id, details)
                VALUES (?, ?, ?, ?)
            """, ("BACKUP_CREATED", "database", backup_filename, f"Created backup at {backup_filepath}"))
    finally:
        conn.close()

    return backup_filepath

def validate_backup_file(backup_filepath: Path) -> bool:
    """Validate that the backup file is a healthy, uncorrupted SQLite database with expected schema."""
    backup_filepath = Path(backup_filepath)
    if not backup_filepath.exists() or backup_filepath.stat().st_size == 0:
        return False
    
    test_conn = None
    try:
        test_conn = sqlite3.connect(f"file:{backup_filepath}?mode=ro", uri=True)
        cursor = test_conn.cursor()
        cursor.execute("PRAGMA integrity_check;")
        res = cursor.fetchone()
        if not res or res[0] != "ok":
            return False

        # Verify required tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = {r[0] for r in cursor.fetchall()}
        required = {"students", "seats", "attendance_events", "settings"}
        return required.issubset(tables)
    except Exception:
        return False
    finally:
        if test_conn:
            test_conn.close()

def list_available_backups() -> List[Dict[str, Any]]:
    """List all available backup files sorted by newest first."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backups = []
    for file in sorted(BACKUP_DIR.glob("*.db"), key=lambda f: f.stat().st_mtime, reverse=True):
        stat = file.stat()
        backups.append({
            "filename": file.name,
            "path": str(file),
            "size_kb": round(stat.st_size / 1024, 2),
            "created_at": datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        })
    return backups

def restore_database_from_backup(backup_filepath: Path) -> Path:
    """
    Restore database from selected backup file.
    Creates a pre-restore safety snapshot before performing the restore.
    """
    backup_filepath = Path(backup_filepath)
    if not backup_filepath.exists():
        raise FileNotFoundError(f"Backup file not found: {backup_filepath}")

    if not validate_backup_file(backup_filepath):
        raise ValueError(f"The selected file '{backup_filepath.name}' is corrupted or not a valid StudySpace backup.")

    # 1. Create pre-restore safety snapshot of the live database
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    safety_name = f"pre_restore_safety_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    safety_copy = BACKUP_DIR / safety_name
    
    if DB_PATH.exists():
        live_conn = get_connection()
        safety_conn = sqlite3.connect(safety_copy)
        try:
            with safety_conn:
                live_conn.backup(safety_conn)
        finally:
            safety_conn.close()
            live_conn.close()

    # 2. Restore backup into live DB
    src_conn = sqlite3.connect(backup_filepath)
    dst_conn = get_connection()
    try:
        with dst_conn:
            src_conn.backup(dst_conn)
    finally:
        src_conn.close()
        dst_conn.close()

    # 3. Log in audit table
    conn = get_connection()
    try:
        cursor = conn.cursor()
        with conn:
            cursor.execute("""
                INSERT INTO audit_logs (action, entity_type, entity_id, details)
                VALUES (?, ?, ?, ?)
            """, ("BACKUP_RESTORED", "database", backup_filepath.name, f"Restored from {backup_filepath.name}. Safety snapshot: {safety_name}"))
    finally:
        conn.close()

    return safety_copy
