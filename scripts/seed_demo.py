import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core.database import init_db, get_connection
from services.student_service import create_student
from services.attendance_service import record_scan_event

def seed_demo_data():
    """Seed clean demo students and sample attendance scans for local evaluation."""
    init_db()
    print("Initializing demo dataset...")

    demo_students = [
        {"name": "Rahul Sharma", "phone": "+91 98765 43210", "seat": "A-12", "notes": "UPSC Aspirant / Morning Shift"},
        {"name": "Priya Patel", "phone": "+91 98123 45678", "seat": "A-04", "notes": "CA Final / Full Day"},
        {"name": "Amit Roy", "phone": "+91 97654 32109", "seat": "B-02", "notes": "State PCS / Evening Shift"},
        {"name": "Neha Singh", "phone": "+91 99887 76655", "seat": "A-06", "notes": "SSC CGL / Regular"},
        {"name": "Vikram Seth", "phone": "+91 91234 56789", "seat": "B-01", "notes": "GATE Study"}
    ]

    created = []
    for s in demo_students:
        try:
            res = create_student(
                full_name=s["name"],
                phone=s["phone"],
                assigned_seat=s["seat"],
                notes=s["notes"]
            )
            created.append(res)
            print(f"Created student: {s['name']} (ID: {res['student_id']}, Seat: {s['seat']})")
        except ValueError as e:
            print(f"Skipping {s['name']}: {e}")

    # Seed sample check-in scans for Rahul and Priya
    if created:
        print("\nRecording initial check-in scans...")
        record_scan_event(created[0]["student_id"], device_id="Station-1")
        if len(created) > 1:
            record_scan_event(created[1]["student_id"], device_id="Station-1")

    print("\nDemo seeding completed successfully.")

if __name__ == "__main__":
    seed_demo_data()
