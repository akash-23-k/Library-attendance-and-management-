import sqlite3
import hashlib
import secrets
from pathlib import Path
from typing import Optional
from core.config import DB_PATH, DEFAULT_LIBRARY_NAME, DEFAULT_COOLDOWN_SECONDS, DEFAULT_ATTENDANCE_MODE

def hash_password(password: str, salt: Optional[str] = None) -> str:
    """Hash password using PBKDF2-HMAC-SHA256 with a unique random salt."""
    if not salt:
        salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )
    return f"{salt}:{key.hex()}"

def verify_password(password: str, stored_hash: str) -> bool:
    """Verify password against stored salt:hash string."""
    try:
        salt, key_hex = stored_hash.split(":", 1)
        test_key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        return secrets.compare_digest(test_key.hex(), key_hex)
    except Exception:
        return False

def get_connection(custom_db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Create and configure a SQLite connection with foreign keys and WAL mode."""
    target_path = custom_db_path or DB_PATH
    conn = sqlite3.connect(target_path, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    return conn

def init_db(custom_db_path: Optional[Path] = None):
    """
    Initialize all database tables, constraints, indexes, default seats, 
    and system settings. Does NOT seed fake students into production.
    """
    conn = get_connection(custom_db_path)
    cursor = conn.cursor()

    # 1. Admins Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'ACTIVE'
        );
    """)

    # 2. Students Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            student_id TEXT PRIMARY KEY,
            full_name TEXT NOT NULL,
            phone TEXT,
            joining_date DATE DEFAULT (DATE('now')),
            assigned_seat TEXT,
            status TEXT DEFAULT 'ACTIVE',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 3. Seats Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS seats (
            seat_id INTEGER PRIMARY KEY AUTOINCREMENT,
            seat_number TEXT UNIQUE NOT NULL,
            zone TEXT NOT NULL,
            status TEXT DEFAULT 'AVAILABLE',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 4. Attendance Events Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance_events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            seat_snapshot TEXT,
            event_type TEXT NOT NULL,
            event_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            device_id TEXT DEFAULT 'Local-Station-1',
            remarks TEXT,
            FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE RESTRICT
        );
    """)

    # 5. Settings Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 6. Audit Logs Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            entity_type TEXT,
            entity_id TEXT,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Performance & Lookup Indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_attendance_student_time ON attendance_events(student_id, event_timestamp);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_attendance_time ON attendance_events(event_timestamp);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_students_assigned_seat ON students(assigned_seat);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_seats_number ON seats(seat_number);")

    conn.commit()

    # Seed Default Settings if missing
    default_settings = [
        ("library_name", DEFAULT_LIBRARY_NAME),
        ("cooldown_seconds", str(DEFAULT_COOLDOWN_SECONDS)),
        ("attendance_mode", DEFAULT_ATTENDANCE_MODE),
    ]
    for key, val in default_settings:
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?);", (key, val))
    conn.commit()

    # Seed Default Admin if none exists (default credentials: admin / admin123)
    cursor.execute("SELECT COUNT(*) as count FROM admins;")
    if cursor.fetchone()["count"] == 0:
        default_hash = hash_password("admin123")
        cursor.execute("INSERT INTO admins (username, password_hash) VALUES (?, ?);", ("admin", default_hash))
        conn.commit()

    # Seed Default Study Desks (Zone A 24 seats, Zone B 24 seats) if empty
    cursor.execute("SELECT COUNT(*) as count FROM seats;")
    if cursor.fetchone()["count"] == 0:
        seats_to_insert = []
        for i in range(1, 25):
            seats_to_insert.append((f"A-{i:02d}", "Zone A (Reading Hall)", "AVAILABLE"))
        for i in range(1, 25):
            seats_to_insert.append((f"B-{i:02d}", "Zone B (Silent Cabin)", "AVAILABLE"))
        
        cursor.executemany(
            "INSERT INTO seats (seat_number, zone, status) VALUES (?, ?, ?);",
            seats_to_insert
        )
        conn.commit()

    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully with production schema.")
