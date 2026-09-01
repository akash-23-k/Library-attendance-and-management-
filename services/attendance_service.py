import datetime
import sqlite3
import time
from typing import Dict, Any, Optional, List
from core.database import get_connection
from core.config import DEFAULT_COOLDOWN_SECONDS

# In-memory scan timestamp cache for instant duplicate prevention
_last_scan_cache: Dict[str, float] = {}

def get_cooldown_seconds() -> int:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = 'cooldown_seconds'")
        row = cursor.fetchone()
        conn.close()
        if row:
            return int(row["value"])
    except Exception:
        pass
    return DEFAULT_COOLDOWN_SECONDS

def record_scan_event(token: str, device_id: str = "Local-Station-1") -> Dict[str, Any]:
    """
    Process a scanned QR token:
    1. Check duplicate scan cooldown.
    2. Lookup student in SQLite.
    3. Determine event_type (CHECK_IN vs CHECK_OUT).
    4. Store event in SQLite and return outcome dictionary.
    """
    token = token.strip()
    now_ts = time.time()
    cooldown = get_cooldown_seconds()

    # 1. Duplicate cooldown check
    if token in _last_scan_cache:
        elapsed = now_ts - _last_scan_cache[token]
        if elapsed < cooldown:
            remaining = int(cooldown - elapsed)
            return {
                "status": "DUPLICATE",
                "message": f"Scan ignored. Duplicate cooldown active ({remaining}s remaining).",
                "token": token
            }

    conn = get_connection()
    cursor = conn.cursor()

    # 2. Lookup student
    cursor.execute("SELECT * FROM students WHERE student_id = ?", (token,))
    student = cursor.fetchone()

    if not student:
        conn.close()
        return {
            "status": "UNREGISTERED",
            "message": f"Unrecognized QR token: [{token}]. Student is not registered.",
            "token": token
        }

    if student["status"] != "ACTIVE":
        conn.close()
        return {
            "status": "INACTIVE",
            "message": f"Student {student['full_name']} is currently marked INACTIVE.",
            "student": dict(student),
            "token": token
        }

    # 3. Determine Check-in vs Check-out
    # Find the latest event for this student today
    today_start = datetime.datetime.now().strftime("%Y-%m-%d 00:00:00")
    cursor.execute("""
        SELECT event_type FROM attendance_events 
        WHERE student_id = ? AND event_timestamp >= ?
        ORDER BY event_id DESC LIMIT 1
    """, (token, today_start))
    
    last_event = cursor.fetchone()
    if last_event and last_event["event_type"] == "CHECK_IN":
        next_event_type = "CHECK_OUT"
    else:
        next_event_type = "CHECK_IN"

    current_time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    seat_snapshot = student["assigned_seat"] or "UNASSIGNED"

    # 4. Insert Attendance Event
    cursor.execute("""
        INSERT INTO attendance_events (student_id, seat_snapshot, event_type, event_timestamp, device_id)
        VALUES (?, ?, ?, ?, ?)
    """, (token, seat_snapshot, next_event_type, current_time_str, device_id))
    
    # Audit log
    cursor.execute("""
        INSERT INTO audit_logs (action, entity_type, entity_id, details)
        VALUES (?, ?, ?, ?)
    """, ("SCAN_EVENT", "attendance", token, f"{next_event_type} at {current_time_str} ({seat_snapshot})"))

    conn.commit()
    conn.close()

    # Update cache
    _last_scan_cache[token] = now_ts

    return {
        "status": "SUCCESS",
        "event_type": next_event_type,
        "message": f"{next_event_type} successfully recorded for {student['full_name']}.",
        "student": dict(student),
        "seat": seat_snapshot,
        "timestamp": current_time_str,
        "token": token
    }

def get_today_metrics() -> Dict[str, Any]:
    """Calculate live dashboard metrics for today."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total FROM students WHERE status = 'ACTIVE'")
    total_students = cursor.fetchone()["total"]

    today_start = datetime.datetime.now().strftime("%Y-%m-%d 00:00:00")
    
    # Total scans today
    cursor.execute("SELECT COUNT(*) as scans FROM attendance_events WHERE event_timestamp >= ?", (today_start,))
    scans_today = cursor.fetchone()["scans"]

    # Active checked-in students right now
    cursor.execute("""
        SELECT student_id, event_type FROM attendance_events
        WHERE event_timestamp >= ?
        ORDER BY event_id ASC
    """, (today_start,))
    
    status_map = {}
    for row in cursor.fetchall():
        status_map[row["student_id"]] = row["event_type"]

    present_count = sum(1 for s, ev in status_map.items() if ev == "CHECK_IN")

    # Seat capacity
    cursor.execute("SELECT COUNT(*) as total_seats FROM seats")
    total_seats = cursor.fetchone()["total_seats"]

    conn.close()

    occupancy_rate = int((present_count / total_seats * 100)) if total_seats > 0 else 0

    return {
        "total_students": total_students,
        "present_count": present_count,
        "total_seats": total_seats,
        "occupancy_rate": occupancy_rate,
        "scans_today": scans_today
    }

def get_recent_scans(limit: int = 10) -> List[Dict[str, Any]]:
    """Get most recent scan logs with student names and seat snapshots."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.event_id, e.event_timestamp, e.student_id, s.full_name, e.seat_snapshot, e.event_type, e.device_id
        FROM attendance_events e
        LEFT JOIN students s ON e.student_id = s.student_id
        ORDER BY e.event_id DESC
        LIMIT ?
    """, (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_seat_occupancy_map() -> Dict[str, Dict[str, Any]]:
    """Return map of seat_number -> {status: 'OCCUPIED'|'AWAY'|'VACANT', student_name: str, token: str}."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT seat_number, zone, status FROM seats ORDER BY seat_number ASC")
    seats = {r["seat_number"]: {"zone": r["zone"], "status": "VACANT", "student": None} for r in cursor.fetchall()}

    cursor.execute("SELECT student_id, full_name, assigned_seat, status FROM students WHERE status = 'ACTIVE' AND assigned_seat IS NOT NULL")
    active_students = {r["assigned_seat"]: dict(r) for r in cursor.fetchall()}

    today_start = datetime.datetime.now().strftime("%Y-%m-%d 00:00:00")
    cursor.execute("""
        SELECT student_id, event_type FROM attendance_events
        WHERE event_timestamp >= ?
        ORDER BY event_id ASC
    """, (today_start,))
    
    presence_map = {}
    for r in cursor.fetchall():
        presence_map[r["student_id"]] = r["event_type"]

    for seat_num, seat_data in seats.items():
        if seat_num in active_students:
            std = active_students[seat_num]
            is_present = (presence_map.get(std["student_id"]) == "CHECK_IN")
            seat_data["status"] = "OCCUPIED" if is_present else "AWAY"
            seat_data["student"] = std

    conn.close()
    return seats
