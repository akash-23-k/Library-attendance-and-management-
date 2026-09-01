import sqlite3
import datetime
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core.config import DB_PATH

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            student_id TEXT PRIMARY KEY,
            full_name TEXT NOT NULL,
            phone TEXT,
            assigned_seat TEXT,
            status TEXT DEFAULT 'ACTIVE',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS seats (
            seat_id INTEGER PRIMARY KEY AUTOINCREMENT,
            seat_number TEXT UNIQUE NOT NULL,
            zone TEXT NOT NULL,
            status TEXT DEFAULT 'AVAILABLE',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance_events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            seat_snapshot TEXT,
            event_type TEXT NOT NULL,
            event_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            device_id TEXT DEFAULT 'Local-Station-1',
            remarks TEXT,
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        );
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_attendance_student ON attendance_events(student_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_attendance_time ON attendance_events(event_timestamp);")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

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

    conn.commit()

    # Seed Default Seats if empty
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

    # Seed initial demo students if empty
    cursor.execute("SELECT COUNT(*) as count FROM students;")
    if cursor.fetchone()["count"] == 0:
        demo_students = [
            ("LIB-8F4K2M", "Rahul Sharma", "+91 98765 43210", "A-12", "ACTIVE", "UPSC Aspirant"),
            ("LIB-9G3M1P", "Priya Patel", "+91 98123 45678", "A-04", "ACTIVE", "CA Final"),
            ("LIB-2D8R5W", "Amit Roy", "+91 97654 32109", "B-02", "ACTIVE", "State PCS"),
            ("LIB-5H2K9Q", "Neha Singh", "+91 99887 76655", "A-06", "ACTIVE", "SSC CGL"),
            ("LIB-7K1P3X", "Vikram Seth", "+91 91234 56789", "B-01", "ACTIVE", "GATE Study")
        ]
        cursor.executemany(
            "INSERT INTO students (student_id, full_name, phone, assigned_seat, status, notes) VALUES (?, ?, ?, ?, ?, ?);",
            demo_students
        )
        for _, _, _, seat, _, _ in demo_students:
            cursor.execute("UPDATE seats SET status = 'OCCUPIED' WHERE seat_number = ?;", (seat,))
        
        conn.commit()

    conn.close()
    print("Database schema and seed initialized.")

if __name__ == '__main__':
    init_db()
