import unittest
import sys
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Use isolated test database
import core.config as config
TEST_DB_PATH = config.DATA_DIR / 'test_library_data.db'
config.DB_PATH = TEST_DB_PATH

import core.database as db_mod
db_mod.DB_PATH = TEST_DB_PATH

import services.backup_service as backup_mod
backup_mod.DB_PATH = TEST_DB_PATH

from core.database import init_db, get_connection
from services.student_service import create_student, list_students, get_student
import services.attendance_service as att_service
from services.attendance_service import record_scan_event, get_today_metrics, get_seat_occupancy_map
from services.qr_service import generate_student_token, generate_qr_image
from services.report_service import get_attendance_logs_dataframe, export_attendance_to_csv, export_attendance_to_excel
from services.backup_service import create_database_backup, list_available_backups

class TestStudySpaceSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Clean previous test DB if any
        if TEST_DB_PATH.exists():
            try:
                os.remove(TEST_DB_PATH)
            except Exception:
                pass
        init_db()

    @classmethod
    def tearDownClass(cls):
        # Clean up test artifacts
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
        # Clear scan cooldown cache for clean test runs
        att_service._last_scan_cache.clear()

    def test_01_student_token_generation(self):
        token = generate_student_token()
        self.assertTrue(token.startswith("LIB-"))
        self.assertEqual(len(token), 10)

    def test_02_create_student_and_qr(self):
        student = create_student(
            full_name="Test Student Automation",
            phone="+91 99999 11111",
            assigned_seat="A-01",
            notes="Automated Unit Test"
        )
        self.assertIsNotNone(student["student_id"])
        self.assertEqual(student["full_name"], "Test Student Automation")
        
        # Verify in DB
        fetched = get_student(student["student_id"])
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["assigned_seat"], "A-01")

    def test_03_seat_conflict_prevention(self):
        # A-01 is held by Test Student Automation, creating another student with A-01 should raise ValueError
        with self.assertRaises(ValueError):
            create_student(
                full_name="Conflict Candidate",
                assigned_seat="A-01"
            )

    def test_04_attendance_checkin_checkout_and_cooldown(self):
        token = "LIB-8F4K2M"  # Seeded student
        
        # 1. First scan -> CHECK_IN
        res1 = record_scan_event(token)
        self.assertEqual(res1["status"], "SUCCESS")
        self.assertEqual(res1["event_type"], "CHECK_IN")
        
        # 2. Immediate second scan should trigger DUPLICATE cooldown protection
        res2 = record_scan_event(token)
        self.assertEqual(res2["status"], "DUPLICATE")

    def test_05_unregistered_qr(self):
        res = record_scan_event("LIB-DOESNOTEXIST-999")
        self.assertEqual(res["status"], "UNREGISTERED")

    def test_06_reports_and_exports(self):
        df = get_attendance_logs_dataframe()
        self.assertIsNotNone(df)

        export_csv_path = BASE_DIR / "data" / "test_export.csv"
        export_excel_path = BASE_DIR / "data" / "test_export.xlsx"

        export_attendance_to_csv(export_csv_path)
        self.assertTrue(export_csv_path.exists())

        export_attendance_to_excel(export_excel_path)
        self.assertTrue(export_excel_path.exists())

    def test_07_database_backup(self):
        backup_path = create_database_backup(label="unittest")
        self.assertTrue(backup_path.exists())
        backups = list_available_backups()
        self.assertGreaterEqual(len(backups), 1)

if __name__ == "__main__":
    unittest.main()
