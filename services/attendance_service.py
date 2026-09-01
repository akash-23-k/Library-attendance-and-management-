import datetime
import sqlite3
import time
from typing import Dict, Any, Optional, List
from core.database import get_connection
from core.config import DEFAULT_COOLDOWN_SECONDS, DEFAULT_ATTENDANCE_MODE

# Level 1 In-memory timestamp cache (cleared on app restart)
_last_scan_cache: Dict[str, float] = {}

def get_system_settings() -> Dict[str, Any]:
    """Retrieve system settings from SQLite with fallbacks."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM settings")
        settings_dict = {r["key"]: r["value"] for r in cursor.fetchall()}
        return {
            "cooldown_seconds": int(settings_dict.get("cooldown_seconds", DEFAULT_COOLDOWN_SECONDS)),
            "attendance_mode": settings_dict.get("attendance_mode", DEFAULT_ATTENDANCE_MODE),
            "library_name": settings_dict.get("library_name", "Apex Study Library")
        }
    finally:
        conn.close()

def record_scan_event(token: str, device_id: str = "Local-Station-1") -> Dict[str, Any]:
    """
    Process a scanned QR token with two-level duplicate protection:
    Level 1: Fast In-memory frame cooldown.
    Level 2: Database-level timestamp validation across app restarts.
    """
    token = token.strip()
    if not token:
        return {"status": "EMPTY", "message": "Empty token received."}

    settings = get_system_settings()
    cooldown = settings["cooldown_seconds"]
    mode = settings["attendance_mode"]
    now_ts = time.time()
    now_dt = datetime.datetime.now()
    now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")
    today_start = now_dt.strftime("%Y-%m-%d 00:00:00")

    # LEVEL 1: In-memory frame cooldown
    if token in _last_scan_cache:
        elapsed = now_ts - _last_scan_cache[token]
        if elapsed < cooldown:
            remaining = int(cooldown - elapsed)
            return {
                "status": "DUPLICATE",
                "message": f"Already scanned — please wait {remaining}s.",
                "token": token,
                "remaining_seconds": remaining
            }

    conn = get_connection()
    try:
        cursor = conn.cursor()

        # 1. Lookup student
        cursor.execute("SELECT * FROM students WHERE student_id = ?", (token,))
        student = cursor.fetchone()

        if not student:
            return {
                "status": "UNREGISTERED",
                "message": f"Unrecognized QR token: [{token}]. Student is not registered.",
                "token": token
            }

        if student["status"] != "ACTIVE":
            return {
                "status": "INACTIVE",
                "message": f"Student '{student['full_name']}' is currently marked INACTIVE.",
                "student": dict(student),
                "token": token
            }

        # LEVEL 2: Database-level cooldown check (resilient across restarts)
        cursor.execute("""
            SELECT event_timestamp, event_type FROM attendance_events 
            WHERE student_id = ? 
            ORDER BY event_id DESC LIMIT 1
        """, (token,))
        last_recorded = cursor.fetchone()

        if last_recorded:
            try:
                last_time = datetime.datetime.strptime(last_recorded["event_timestamp"], "%Y-%m-%d %H:%M:%S")
                db_elapsed = (now_dt - last_time).total_seconds()
                if 0 <= db_elapsed < cooldown:
                    remaining = int(cooldown - db_elapsed)
                    return {
                        "status": "DUPLICATE",
                        "message": f"Already scanned — please wait {remaining}s.",
                        "token": token,
                        "remaining_seconds": remaining
                    }
            except Exception:
                pass  # If timestamp format differs, proceed safely

        # 2. Determine Attendance Event Type
        if mode == "DAILY_PRESENCE":
            cursor.execute("""
                SELECT event_id, event_timestamp FROM attendance_events 
                WHERE student_id = ? AND event_timestamp >= ?
                LIMIT 1
            """, (token, today_start))
            today_event = cursor.fetchone()
            if today_event:
                return {
                    "status": "DUPLICATE",
                    "message": f"Daily presence already recorded today for {student['full_name']}.",
                    "token": token,
                    "student": dict(student)
                }
            next_event_type = "CHECK_IN"
        else:
            # CHECKIN_CHECKOUT mode: check today's latest event
            cursor.execute("""
                SELECT event_type FROM attendance_events 
                WHERE student_id = ? AND event_timestamp >= ?
                ORDER BY event_id DESC LIMIT 1
            """, (token, today_start))
            latest_today = cursor.fetchone()

            if latest_today and latest_today["event_type"] == "CHECK_IN":
                next_event_type = "CHECK_OUT"
            else:
                next_event_type = "CHECK_IN"

        seat_snapshot = student["assigned_seat"] or "UNASSIGNED"

        # 3. Atomic Database Insertion
        with conn:
            cursor.execute("""
                INSERT INTO attendance_events (student_id, seat_snapshot, event_type, event_timestamp, device_id)
                VALUES (?, ?, ?, ?, ?)
            """, (token, seat_snapshot, next_event_type, now_str, device_id))

            cursor.execute("""
                INSERT INTO audit_logs (action, entity_type, entity_id, details)
                VALUES (?, ?, ?, ?)
            """, ("SCAN_EVENT", "attendance", token, f"{next_event_type} at {now_str} (Seat: {seat_snapshot})"))

        # Update in-memory cache
        _last_scan_cache[token] = now_ts

        return {
            "status": "SUCCESS",
            "event_type": next_event_type,
            "message": f"{next_event_type} successfully recorded for {student['full_name']}.",
            "student": dict(student),
            "seat": seat_snapshot,
            "timestamp": now_str,
            "token": token
        }
    finally:
        conn.close()

def get_today_metrics() -> Dict[str, Any]:
    """Calculate operational dashboard metrics for today."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        today_start = datetime.datetime.now().strftime("%Y-%m-%d 00:00:00")

        # 1. Total Active Students
        cursor.execute("SELECT COUNT(*) as total FROM students WHERE status = 'ACTIVE'")
        total_students = cursor.fetchone()["total"]

        # 2. Total Scans Today
        cursor.execute("SELECT COUNT(*) as scans FROM attendance_events WHERE event_timestamp >= ?", (today_start,))
        scans_today = cursor.fetchone()["scans"]

        # 3. Present Students Count (latest event today is CHECK_IN)
        cursor.execute("""
            SELECT student_id, event_type FROM attendance_events
            WHERE event_timestamp >= ?
            ORDER BY event_id ASC
        """, (today_start,))
        
        status_map = {}
        for row in cursor.fetchall():
            status_map[row["student_id"]] = row["event_type"]

        present_count = sum(1 for s, ev in status_map.items() if ev == "CHECK_IN")

        # 4. Total Seats & Available Seats
        cursor.execute("SELECT COUNT(*) as total FROM seats")
        total_seats = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT COUNT(*) as available FROM seats 
            WHERE status = 'AVAILABLE' AND seat_number NOT IN (
                SELECT assigned_seat FROM students 
                WHERE status = 'ACTIVE' AND assigned_seat IS NOT NULL AND assigned_seat != ''
            )
        """)
        available_seats = cursor.fetchone()["available"]

        occupancy_rate = int((present_count / total_seats * 100)) if total_seats > 0 else 0

        return {
            "total_students": total_students,
            "present_count": present_count,
            "total_seats": total_seats,
            "available_seats": available_seats,
            "occupancy_rate": occupancy_rate,
            "scans_today": scans_today
        }
    finally:
        conn.close()

def get_recent_scans(limit: int = 10) -> List[Dict[str, Any]]:
    """Retrieve most recent attendance events with student details."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.event_id, e.event_timestamp, e.student_id, s.full_name, e.seat_snapshot, e.event_type, e.device_id
            FROM attendance_events e
            LEFT JOIN students s ON e.student_id = s.student_id
            ORDER BY e.event_id DESC
            LIMIT ?
        """, (limit,))
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()

def get_seat_occupancy_map() -> Dict[str, Dict[str, Any]]:
    """
    Return mapped study desks with visual occupancy distinction:
    - 'VACANT': Seat is not assigned to any active student.
    - 'PRESENT': Seat is assigned to student who is currently checked-in today.
    - 'AWAY': Seat is assigned to student who is currently away/checked-out.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        today_start = datetime.datetime.now().strftime("%Y-%m-%d 00:00:00")

        cursor.execute("SELECT seat_number, zone, status FROM seats ORDER BY seat_number ASC")
        seats = {r["seat_number"]: {"zone": r["zone"], "status": "VACANT", "student": None} for r in cursor.fetchall()}

        cursor.execute("SELECT student_id, full_name, assigned_seat, phone, status FROM students WHERE status = 'ACTIVE' AND assigned_seat IS NOT NULL AND assigned_seat != ''")
        active_assigned = {r["assigned_seat"]: dict(r) for r in cursor.fetchall()}

        cursor.execute("""
            SELECT student_id, event_type FROM attendance_events
            WHERE event_timestamp >= ?
            ORDER BY event_id ASC
        """, (today_start,))
        
        presence_map = {}
        for r in cursor.fetchall():
            presence_map[r["student_id"]] = r["event_type"]

        for seat_num, seat_data in seats.items():
            if seat_num in active_assigned:
                std = active_assigned[seat_num]
                is_present = (presence_map.get(std["student_id"]) == "CHECK_IN")
                seat_data["status"] = "PRESENT" if is_present else "AWAY"
                seat_data["student"] = std

        return seats
    finally:
        conn.close()
