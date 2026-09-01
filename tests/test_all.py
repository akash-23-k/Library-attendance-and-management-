import unittest
import sys
import os
import time
import datetime
from pathlib import Path
import sqlite3

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Use isolated test database
import core.config as config
TEST_DB_PATH = config.DATA_DIR / 'test_isolated_library.db'
config.DB_PATH = TEST_DB_PATH

import core.database as db_mod
db_mod.DB_PATH = TEST_DB_PATH

import services.backup_service as backup_mod
backup_mod.DB_PATH = TEST_DB_PATH

from core.database import init_db, get_connection, hash_password, verify_password
from services.auth_service import authenticate_admin, change_admin_password
from services.student_service import create_student, list_students, get_student, update_student, toggle_student_status, get_available_seats
import services.attendance_service as att_service
from services.attendance_service import record_scan_event, get_today_metrics, get_seat_occupancy_map
from services.qr_service import generate_student_token, generate_qr_image, generate_student_id_card
from services.report_service import get_attendance_logs_dataframe, get_student_summary_dataframe, export_attendance_to_csv, export_attendance_to_excel
from services.backup_service import create_database_backup, list_available_backups, restore_database_from_backup, validate_backup_file

class TestCompleteLibrarySystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if TEST_DB_PATH.exists():
            try:
                os.remove(TEST_DB_PATH)
            except Exception:
                pass
        init_db()

    @classmethod
    def tearDownClass(cls):
        for p in [
            TEST_DB_PATH,
            BASE_DIR / "data" / "test_export.csv",
            BASE_DIR / "data" / "test_export.xlsx"
        ]:
            if p.exists():
                try:
                    os.remove(p)
                except Exception:
                    pass

    def setUp(self):
        att_service._last_scan_cache.clear()

    # ==================== 1. DATABASE & AUTHENTICATION ====================
    def test_01_schema_and_admin_auth(self):
        # Verify default admin seeded
        admin = authenticate_admin("admin", "admin123")
        self.assertIsNotNone(admin)
        self.assertEqual(admin["username"], "admin")

        # Verify failed login
        self.assertIsNone(authenticate_admin("admin", "wrongpassword"))
        self.assertIsNone(authenticate_admin("nonexistent_user", "admin123"))

        # Verify password change
        res = change_admin_password("admin", "admin123", "newsecret123")
        self.assertTrue(res)
        self.assertIsNotNone(authenticate_admin("admin", "newsecret123"))
        
        # Reset back for clean state
        change_admin_password("admin", "newsecret123", "admin123")

    def test_02_foreign_key_and_transactions(self):
        conn = get_connection()
        cursor = conn.cursor()
        
        # Attempt to insert attendance event for non-existent student should fail FK constraint
        with self.assertRaises(sqlite3.IntegrityError):
            with conn:
                cursor.execute("""
                    INSERT INTO attendance_events (student_id, seat_snapshot, event_type)
                    VALUES ('LIB-DOESNOTEXIST', 'A-01', 'CHECK_IN')
                """)
        conn.close()

    # ==================== 2. STUDENT & SEAT MANAGEMENT ====================
    def test_03_create_student_and_seat_sync(self):
        # Create student with assigned seat A-01
        student = create_student(
            full_name="Rajesh Khanna",
            phone="+91 98765 11111",
            assigned_seat="A-01",
            notes="Unit Test Student"
        )
        self.assertTrue(student["student_id"].startswith("LIB-"))
        self.assertEqual(student["assigned_seat"], "A-01")

        # Verify seat A-01 is marked OCCUPIED in seats table
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT status FROM seats WHERE seat_number = 'A-01'")
        self.assertEqual(c.fetchone()["status"], "OCCUPIED")
        conn.close()

        # Attempt to assign the same seat A-01 to another student must fail
        with self.assertRaises(ValueError):
            create_student(
                full_name="Conflicting Student",
                assigned_seat="A-01"
            )

    def test_04_update_student_and_seat_reassignment(self):
        student = create_student(
            full_name="Sunita Rao",
            phone="+91 98765 22222",
            assigned_seat="A-02"
        )
        std_id = student["student_id"]

        # Reassign Sunita from A-02 to A-03
        update_student(
            student_id=std_id,
            full_name="Sunita Rao",
            assigned_seat="A-03",
            status="ACTIVE"
        )

        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT status FROM seats WHERE seat_number = 'A-02'")
        self.assertEqual(c.fetchone()["status"], "AVAILABLE")  # Old seat released
        c.execute("SELECT status FROM seats WHERE seat_number = 'A-03'")
        self.assertEqual(c.fetchone()["status"], "OCCUPIED")   # New seat occupied
        conn.close()

    def test_05_student_deactivation_releases_seat(self):
        student = create_student(
            full_name="Manoj Verma",
            assigned_seat="A-05"
        )
        std_id = student["student_id"]

        # Toggle to INACTIVE
        new_status = toggle_student_status(std_id)
        self.assertEqual(new_status, "INACTIVE")

        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT status FROM seats WHERE seat_number = 'A-05'")
        self.assertEqual(c.fetchone()["status"], "AVAILABLE")  # Seat freed
        conn.close()

        # Inactive student cannot scan attendance
        scan_res = record_scan_event(std_id)
        self.assertEqual(scan_res["status"], "INACTIVE")

    # ==================== 3. ATTENDANCE & DUPLICATE PROTECTION ====================
    def test_06_attendance_checkin_checkout_toggle(self):
        student = create_student(
            full_name="Kavita Krishnan",
            assigned_seat="B-05"
        )
        token = student["student_id"]

        # 1. First Scan -> CHECK_IN
        res1 = record_scan_event(token)
        self.assertEqual(res1["status"], "SUCCESS")
        self.assertEqual(res1["event_type"], "CHECK_IN")
        self.assertEqual(res1["seat"], "B-05")

        # 2. Immediate frame scan -> Level 1 in-memory duplicate cooldown
        res_dup1 = record_scan_event(token)
        self.assertEqual(res_dup1["status"], "DUPLICATE")

        # 3. Simulate App Restart by clearing in-memory cache -> Level 2 database cooldown check
        att_service._last_scan_cache.clear()
        res_dup2 = record_scan_event(token)
        self.assertEqual(res_dup2["status"], "DUPLICATE")
        self.assertIn("Already scanned", res_dup2["message"])

    def test_07_seat_snapshot_immutability(self):
        student = create_student(
            full_name="Deepak Sharma",
            assigned_seat="B-10"
        )
        token = student["student_id"]

        # Record scan with seat snapshot B-10
        res = record_scan_event(token)
        self.assertEqual(res["seat"], "B-10")

        # Now change Deepak's assigned seat to B-11
        update_student(
            student_id=token,
            full_name="Deepak Sharma",
            assigned_seat="B-11"
        )

        # Historical attendance log must still show B-10
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT seat_snapshot FROM attendance_events WHERE student_id = ? ORDER BY event_id DESC LIMIT 1", (token,))
        self.assertEqual(c.fetchone()["seat_snapshot"], "B-10")
        conn.close()

    def test_08_unknown_qr_rejection(self):
        res = record_scan_event("LIB-INVALID-TOKEN-999")
        self.assertEqual(res["status"], "UNREGISTERED")

    # ==================== 4. REPORTING & EXPORTS ====================
    def test_09_export_csv_and_excel(self):
        csv_file = BASE_DIR / "data" / "test_export.csv"
        excel_file = BASE_DIR / "data" / "test_export.xlsx"

        out_csv = export_attendance_to_csv(csv_file)
        self.assertTrue(Path(out_csv).exists())
        self.assertGreater(Path(out_csv).stat().st_size, 0)

        out_excel = export_attendance_to_excel(excel_file)
        self.assertTrue(Path(out_excel).exists())
        self.assertGreater(Path(out_excel).stat().st_size, 0)

    # ==================== 5. BACKUP & RESTORE ====================
    def test_10_database_backup_and_safe_restore(self):
        # 1. Create backup
        backup_path = create_database_backup(label="unittest")
        self.assertTrue(backup_path.exists())
        self.assertTrue(validate_backup_file(backup_path))

        # 2. Verify invalid backup rejection
        fake_backup = BASE_DIR / "data" / "fake_corrupt.db"
        with open(fake_backup, "wb") as f:
            f.write(b"NOT A VALID SQLITE DATABASE")
        self.assertFalse(validate_backup_file(fake_backup))
        with self.assertRaises(ValueError):
            restore_database_from_backup(fake_backup)
        os.remove(fake_backup)

        # 3. Restore valid backup
        safety_copy = restore_database_from_backup(backup_path)
        self.assertTrue(safety_copy.exists())

if __name__ == "__main__":
    unittest.main()
