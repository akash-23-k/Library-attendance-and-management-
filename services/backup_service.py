import sqlite3
import shutil
import datetime
from pathlib import Path
from typing import List, Dict, Any
from core.config import DB_PATH, BACKUP_DIR
from core.database import get_connection

def create_database_backup(label: str = "manual") -> Path:
    """
    Perform a consistent SQLite online backup to data/backups/
    """
    timestamp = datetime.datetime.now().strftime("%Y_%m_%d_%H%M%S")
    backup_filename = f"backup_{timestamp}_{label}.db"
    backup_filepath = BACKUP_DIR / backup_filename

    src_conn = get_connection()
    dst_conn = sqlite3.connect(backup_filepath)
    
    with dst_conn:
        src_conn.backup(dst_conn, pages=100)
    
    dst_conn.close()
    src_conn.close()

    # Log in audit table
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO audit_logs (action, entity_type, entity_id, details)
        VALUES (?, ?, ?, ?)
    """, ("BACKUP_CREATED", "database", backup_filename, f"Created backup at {backup_filepath}"))
    conn.commit()
    conn.close()

    return backup_filepath

def list_available_backups() -> List[Dict[str, Any]]:
    """List all available backup files sorted by creation time descending."""
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
    Always creates a pre-restore safety copy first.
    """
    if not backup_filepath.exists():
        raise FileNotFoundError(f"Backup file not found: {backup_filepath}")

    # 1. Create safety snapshot of current live DB
    safety_copy = DB_PATH.parent / f"pre_restore_safety_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    shutil.copy2(DB_PATH, safety_copy)

    # 2. Restore selected backup into live DB
    src_conn = sqlite3.connect(backup_filepath)
    dst_conn = sqlite3.connect(DB_PATH)
    
    with dst_conn:
        src_conn.backup(dst_conn)
        
    src_conn.close()
    dst_conn.close()

    return safety_copy
