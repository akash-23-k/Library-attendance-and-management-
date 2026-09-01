from typing import List, Dict, Any, Optional
from core.database import get_connection
from services.qr_service import generate_student_token, generate_student_id_card

def list_students(query: Optional[str] = None, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """Search and filter student records."""
    conn = get_connection()
    cursor = conn.cursor()
    sql = "SELECT * FROM students WHERE 1=1"
    params = []

    if status_filter and status_filter != "ALL":
        sql += " AND status = ?"
        params.append(status_filter)

    if query:
        query_pattern = f"%{query}%"
        sql += " AND (full_name LIKE ? OR student_id LIKE ? OR assigned_seat LIKE ? OR phone LIKE ?)"
        params.extend([query_pattern, query_pattern, query_pattern, query_pattern])

    sql += " ORDER BY created_at DESC"
    cursor.execute(sql, params)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_student(student_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students WHERE student_id = ?", (student_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_available_seats() -> List[Dict[str, Any]]:
    """Return list of seats that are currently unassigned to any active student."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.seat_number, s.zone 
        FROM seats s
        WHERE s.seat_number NOT IN (
            SELECT assigned_seat FROM students 
            WHERE status = 'ACTIVE' AND assigned_seat IS NOT NULL
        )
        ORDER BY s.seat_number ASC
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def create_student(full_name: str, phone: str = "", assigned_seat: str = "", notes: str = "", library_name: str = "Apex Study Library") -> Dict[str, Any]:
    """Register a new student, assign seat, and auto-generate QR pass card."""
    token = generate_student_token()
    conn = get_connection()
    cursor = conn.cursor()

    # Prevent seat conflict
    if assigned_seat:
        cursor.execute("SELECT full_name FROM students WHERE assigned_seat = ? AND status = 'ACTIVE'", (assigned_seat,))
        existing = cursor.fetchone()
        if existing:
            conn.close()
            raise ValueError(f"Seat {assigned_seat} is already held by active student '{existing['full_name']}'.")

    cursor.execute("""
        INSERT INTO students (student_id, full_name, phone, assigned_seat, status, notes)
        VALUES (?, ?, ?, ?, 'ACTIVE', ?)
    """, (token, full_name, phone, assigned_seat, notes))

    if assigned_seat:
        cursor.execute("UPDATE seats SET status = 'OCCUPIED' WHERE seat_number = ?", (assigned_seat,))

    # Log action
    cursor.execute("""
        INSERT INTO audit_logs (action, entity_type, entity_id, details)
        VALUES (?, ?, ?, ?)
    """, ("STUDENT_CREATED", "student", token, f"Created {full_name}, Seat: {assigned_seat}"))

    conn.commit()
    conn.close()

    # Generate QR Pass Card file
    card_path = generate_student_id_card(token, full_name, assigned_seat or "UNASSIGNED", library_name)

    return {
        "student_id": token,
        "full_name": full_name,
        "phone": phone,
        "assigned_seat": assigned_seat,
        "status": "ACTIVE",
        "notes": notes,
        "qr_card_path": str(card_path)
    }

def update_student(student_id: str, full_name: str, phone: str, assigned_seat: str, status: str, notes: str) -> None:
    conn = get_connection()
    cursor = conn.cursor()

    # Check previous seat
    cursor.execute("SELECT assigned_seat, status FROM students WHERE student_id = ?", (student_id,))
    prev = cursor.fetchone()
    prev_seat = prev["assigned_seat"] if prev else None

    # Check seat conflict if changing seat
    if assigned_seat and assigned_seat != prev_seat:
        cursor.execute("SELECT student_id, full_name FROM students WHERE assigned_seat = ? AND status = 'ACTIVE' AND student_id != ?", (assigned_seat, student_id))
        conflict = cursor.fetchone()
        if conflict:
            conn.close()
            raise ValueError(f"Seat {assigned_seat} is currently held by '{conflict['full_name']}'.")

    cursor.execute("""
        UPDATE students
        SET full_name = ?, phone = ?, assigned_seat = ?, status = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
        WHERE student_id = ?
    """, (full_name, phone, assigned_seat, status, notes, student_id))

    cursor.execute("""
        INSERT INTO audit_logs (action, entity_type, entity_id, details)
        VALUES (?, ?, ?, ?)
    """, ("STUDENT_UPDATED", "student", student_id, f"Updated info: {full_name}, Seat: {assigned_seat}, Status: {status}"))

    conn.commit()
    conn.close()

def toggle_student_status(student_id: str) -> str:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM students WHERE student_id = ?", (student_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise ValueError("Student not found")
    new_status = "INACTIVE" if row["status"] == "ACTIVE" else "ACTIVE"
    cursor.execute("UPDATE students SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE student_id = ?", (new_status, student_id))
    cursor.execute("""
        INSERT INTO audit_logs (action, entity_type, entity_id, details)
        VALUES (?, ?, ?, ?)
    """, ("STATUS_TOGGLE", "student", student_id, f"Changed status to {new_status}"))
    conn.commit()
    conn.close()
    return new_status
