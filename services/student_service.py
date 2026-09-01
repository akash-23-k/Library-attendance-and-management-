import datetime
from typing import List, Dict, Any, Optional
from core.database import get_connection
from services.qr_service import generate_student_token, generate_student_id_card

def list_students(query: Optional[str] = None, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """Search and filter student records ordered by newest first."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        sql = "SELECT * FROM students WHERE 1=1"
        params = []

        if status_filter and status_filter != "ALL":
            sql += " AND status = ?"
            params.append(status_filter)

        if query:
            pattern = f"%{query.strip()}%"
            sql += " AND (full_name LIKE ? OR student_id LIKE ? OR assigned_seat LIKE ? OR phone LIKE ?)"
            params.extend([pattern, pattern, pattern, pattern])

        sql += " ORDER BY created_at DESC"
        cursor.execute(sql, params)
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()

def get_student(student_id: str) -> Optional[Dict[str, Any]]:
    """Lookup student by unique token."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE student_id = ?", (student_id.strip(),))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def get_available_seats() -> List[Dict[str, Any]]:
    """Return list of seats that are currently unassigned to any active student."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.seat_number, s.zone 
            FROM seats s
            WHERE s.seat_number NOT IN (
                SELECT assigned_seat FROM students 
                WHERE status = 'ACTIVE' AND assigned_seat IS NOT NULL AND assigned_seat != ''
            )
            ORDER BY s.seat_number ASC
        """)
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()

def create_student(full_name: str, phone: str = "", assigned_seat: str = "", notes: str = "", joining_date: Optional[str] = None, library_name: str = "Apex Study Library") -> Dict[str, Any]:
    """
    Register a new student, assign seat, synchronize seat status, and auto-generate QR passcard.
    Guaranteed atomic database transaction.
    """
    full_name = full_name.strip()
    if not full_name:
        raise ValueError("Student full name cannot be empty.")

    assigned_seat = assigned_seat.strip() if assigned_seat else None
    phone = phone.strip() if phone else None
    notes = notes.strip() if notes else None
    if not joining_date:
        joining_date = datetime.date.today().isoformat()

    conn = get_connection()
    try:
        cursor = conn.cursor()
        with conn:
            # 1. Generate unique token with collision guard
            token = None
            for _ in range(10):
                candidate = generate_student_token()
                cursor.execute("SELECT 1 FROM students WHERE student_id = ?", (candidate,))
                if not cursor.fetchone():
                    token = candidate
                    break
            if not token:
                raise RuntimeError("Failed to generate a unique student token. Please retry.")

            # 2. Check seat availability if seat is requested
            if assigned_seat:
                # Check seat exists
                cursor.execute("SELECT seat_number FROM seats WHERE seat_number = ?", (assigned_seat,))
                if not cursor.fetchone():
                    raise ValueError(f"Seat '{assigned_seat}' does not exist in library seat configuration.")

                # Check seat conflict with active students
                cursor.execute("SELECT full_name FROM students WHERE assigned_seat = ? AND status = 'ACTIVE'", (assigned_seat,))
                existing = cursor.fetchone()
                if existing:
                    raise ValueError(f"Seat '{assigned_seat}' is already held by active student '{existing['full_name']}'.")

                # Mark seat occupied
                cursor.execute("UPDATE seats SET status = 'OCCUPIED', updated_at = CURRENT_TIMESTAMP WHERE seat_number = ?", (assigned_seat,))

            # 3. Insert student record
            cursor.execute("""
                INSERT INTO students (student_id, full_name, phone, joining_date, assigned_seat, status, notes)
                VALUES (?, ?, ?, ?, ?, 'ACTIVE', ?)
            """, (token, full_name, phone, joining_date, assigned_seat, notes))

            # 4. Audit Log
            cursor.execute("""
                INSERT INTO audit_logs (action, entity_type, entity_id, details)
                VALUES (?, ?, ?, ?)
            """, ("STUDENT_CREATED", "student", token, f"Created {full_name}, Seat: {assigned_seat or 'None'}, Phone: {phone or 'None'}"))

        # Generate printable QR pass card
        card_path = generate_student_id_card(token, full_name, assigned_seat or "UNASSIGNED", library_name)

        return {
            "student_id": token,
            "full_name": full_name,
            "phone": phone,
            "joining_date": joining_date,
            "assigned_seat": assigned_seat,
            "status": "ACTIVE",
            "notes": notes,
            "qr_card_path": str(card_path)
        }
    finally:
        conn.close()

def update_student(student_id: str, full_name: str, phone: str = "", assigned_seat: str = "", status: str = "ACTIVE", notes: str = "") -> Dict[str, Any]:
    """
    Update student details and synchronize seat occupancy state atomically.
    """
    student_id = student_id.strip()
    full_name = full_name.strip()
    if not full_name:
        raise ValueError("Student full name cannot be empty.")

    assigned_seat = assigned_seat.strip() if assigned_seat else None
    phone = phone.strip() if phone else None
    notes = notes.strip() if notes else None
    status = status.strip().upper()
    if status not in ("ACTIVE", "INACTIVE"):
        raise ValueError("Status must be either 'ACTIVE' or 'INACTIVE'.")

    conn = get_connection()
    try:
        cursor = conn.cursor()
        with conn:
            cursor.execute("SELECT * FROM students WHERE student_id = ?", (student_id,))
            student = cursor.fetchone()
            if not student:
                raise ValueError(f"Student with ID '{student_id}' not found.")

            old_seat = student["assigned_seat"]
            old_status = student["status"]

            # Seat reassignment / conflict logic
            if status == "ACTIVE":
                if assigned_seat:
                    # Check seat existence
                    cursor.execute("SELECT seat_number FROM seats WHERE seat_number = ?", (assigned_seat,))
                    if not cursor.fetchone():
                        raise ValueError(f"Seat '{assigned_seat}' does not exist.")

                    # Check conflict if seat changed or reactivated
                    if assigned_seat != old_seat or old_status != "ACTIVE":
                        cursor.execute("""
                            SELECT student_id, full_name FROM students 
                            WHERE assigned_seat = ? AND status = 'ACTIVE' AND student_id != ?
                        """, (assigned_seat, student_id))
                        conflict = cursor.fetchone()
                        if conflict:
                            raise ValueError(f"Seat '{assigned_seat}' is currently held by '{conflict['full_name']}'.")

                    # Occupy new seat
                    cursor.execute("UPDATE seats SET status = 'OCCUPIED', updated_at = CURRENT_TIMESTAMP WHERE seat_number = ?", (assigned_seat,))

                # If seat was removed or changed, free old seat
                if old_seat and old_seat != assigned_seat:
                    cursor.execute("UPDATE seats SET status = 'AVAILABLE', updated_at = CURRENT_TIMESTAMP WHERE seat_number = ?", (old_seat,))

            elif status == "INACTIVE":
                # Deactivated student releases seat
                if old_seat:
                    cursor.execute("UPDATE seats SET status = 'AVAILABLE', updated_at = CURRENT_TIMESTAMP WHERE seat_number = ?", (old_seat,))

            # Update student record
            cursor.execute("""
                UPDATE students
                SET full_name = ?, phone = ?, assigned_seat = ?, status = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
                WHERE student_id = ?
            """, (full_name, phone, assigned_seat, status, notes, student_id))

            # Audit Log
            cursor.execute("""
                INSERT INTO audit_logs (action, entity_type, entity_id, details)
                VALUES (?, ?, ?, ?)
            """, ("STUDENT_UPDATED", "student", student_id, f"Updated: {full_name}, Seat: {assigned_seat or 'None'}, Status: {status}"))

        return {
            "student_id": student_id,
            "full_name": full_name,
            "phone": phone,
            "assigned_seat": assigned_seat,
            "status": status,
            "notes": notes
        }
    finally:
        conn.close()

def toggle_student_status(student_id: str) -> str:
    """Toggle a student's active status and update seat availability."""
    student_id = student_id.strip()
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE student_id = ?", (student_id,))
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Student with ID '{student_id}' not found.")

        current_status = row["status"]
        target_status = "INACTIVE" if current_status == "ACTIVE" else "ACTIVE"
        assigned_seat = row["assigned_seat"]

        with conn:
            if target_status == "ACTIVE" and assigned_seat:
                # Validate seat is not taken by someone else
                cursor.execute("""
                    SELECT full_name FROM students 
                    WHERE assigned_seat = ? AND status = 'ACTIVE' AND student_id != ?
                """, (assigned_seat, student_id))
                conflict = cursor.fetchone()
                if conflict:
                    raise ValueError(f"Cannot reactivate student: Seat '{assigned_seat}' is now held by '{conflict['full_name']}'. Please reassign seat first.")
                cursor.execute("UPDATE seats SET status = 'OCCUPIED', updated_at = CURRENT_TIMESTAMP WHERE seat_number = ?", (assigned_seat,))
            elif target_status == "INACTIVE" and assigned_seat:
                # Release seat
                cursor.execute("UPDATE seats SET status = 'AVAILABLE', updated_at = CURRENT_TIMESTAMP WHERE seat_number = ?", (assigned_seat,))

            cursor.execute("""
                UPDATE students 
                SET status = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE student_id = ?
            """, (target_status, student_id))

            cursor.execute("""
                INSERT INTO audit_logs (action, entity_type, entity_id, details)
                VALUES (?, ?, ?, ?)
            """, ("STATUS_TOGGLE", "student", student_id, f"Changed status from {current_status} to {target_status}"))

        return target_status
    finally:
        conn.close()
