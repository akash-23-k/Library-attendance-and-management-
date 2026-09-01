import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
import pandas as pd
from core.database import get_connection

def get_attendance_logs_dataframe(
    start_date: Optional[str] = None, 
    end_date: Optional[str] = None, 
    student_query: Optional[str] = None,
    seat_filter: Optional[str] = None,
    event_type_filter: Optional[str] = None
) -> pd.DataFrame:
    """Query raw attendance events with filters and return as formatted pandas DataFrame."""
    conn = get_connection()
    try:
        sql = """
            SELECT 
                e.event_id AS "Event ID",
                e.event_timestamp AS "Timestamp",
                e.student_id AS "Student Token",
                s.full_name AS "Student Name",
                s.phone AS "Contact Phone",
                e.seat_snapshot AS "Seat Snapshot",
                e.event_type AS "Event Type",
                e.device_id AS "Device ID"
            FROM attendance_events e
            LEFT JOIN students s ON e.student_id = s.student_id
            WHERE 1=1
        """
        params = []
        if start_date:
            sql += " AND e.event_timestamp >= ?"
            params.append(f"{start_date} 00:00:00")
        if end_date:
            sql += " AND e.event_timestamp <= ?"
            params.append(f"{end_date} 23:59:59")
        if student_query:
            pattern = f"%{student_query.strip()}%"
            sql += " AND (s.full_name LIKE ? OR e.student_id LIKE ?)"
            params.extend([pattern, pattern])
        if seat_filter and seat_filter != "ALL":
            sql += " AND e.seat_snapshot = ?"
            params.append(seat_filter.strip())
        if event_type_filter and event_type_filter != "ALL":
            sql += " AND e.event_type = ?"
            params.append(event_type_filter.strip())

        sql += " ORDER BY e.event_id DESC"
        df = pd.read_sql_query(sql, conn, params=params)
        return df
    finally:
        conn.close()

def get_student_summary_dataframe(start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
    """Calculate aggregated attendance metrics per student."""
    conn = get_connection()
    try:
        sql = """
            SELECT 
                e.student_id,
                s.full_name,
                s.assigned_seat,
                s.status,
                e.event_type,
                e.event_timestamp
            FROM attendance_events e
            JOIN students s ON e.student_id = s.student_id
            WHERE 1=1
        """
        params = []
        if start_date:
            sql += " AND e.event_timestamp >= ?"
            params.append(f"{start_date} 00:00:00")
        if end_date:
            sql += " AND e.event_timestamp <= ?"
            params.append(f"{end_date} 23:59:59")

        df_events = pd.read_sql_query(sql, conn, params=params)

        if df_events.empty:
            return pd.DataFrame(columns=[
                "Student Name", "Student Token", "Assigned Seat", "Status", 
                "Days Present", "Check-Ins", "Check-Outs", "Total Scans", "Last Seen"
            ])

        summary_rows = []
        for (std_id, name, seat, status), group in df_events.groupby(["student_id", "full_name", "assigned_seat", "status"]):
            group["date"] = pd.to_datetime(group["event_timestamp"]).dt.date
            days_present = group["date"].nunique()
            check_ins = (group["event_type"] == "CHECK_IN").sum()
            check_outs = (group["event_type"] == "CHECK_OUT").sum()
            total_scans = len(group)
            last_seen = group["event_timestamp"].max()
            summary_rows.append({
                "Student Name": name,
                "Student Token": std_id,
                "Assigned Seat": seat or "Unassigned",
                "Status": status,
                "Days Present": int(days_present),
                "Check-Ins": int(check_ins),
                "Check-Outs": int(check_outs),
                "Total Scans": int(total_scans),
                "Last Seen": last_seen
            })

        return pd.DataFrame(summary_rows)
    finally:
        conn.close()

def get_students_master_dataframe() -> pd.DataFrame:
    """Retrieve full student directory as DataFrame."""
    conn = get_connection()
    try:
        sql = """
            SELECT 
                student_id AS "Student Token",
                full_name AS "Full Name",
                phone AS "Contact Phone",
                joining_date AS "Joining Date",
                assigned_seat AS "Assigned Seat",
                status AS "Status",
                notes AS "Notes",
                created_at AS "Created At"
            FROM students
            ORDER BY full_name ASC
        """
        return pd.read_sql_query(sql, conn)
    finally:
        conn.close()

def export_attendance_to_csv(
    filepath: Path, 
    start_date: Optional[str] = None, 
    end_date: Optional[str] = None,
    student_query: Optional[str] = None,
    seat_filter: Optional[str] = None,
    event_type_filter: Optional[str] = None
) -> str:
    """Export filtered attendance logs to a standard CSV file with UTF-8 BOM."""
    try:
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        df = get_attendance_logs_dataframe(start_date, end_date, student_query, seat_filter, event_type_filter)
        df.to_csv(filepath, index=False, encoding="utf-8-sig")
        return str(filepath)
    except PermissionError:
        raise PermissionError(f"Cannot write to '{filepath.name}'. The file may be open in Excel or another program.")

def export_attendance_to_excel(
    filepath: Path, 
    start_date: Optional[str] = None, 
    end_date: Optional[str] = None,
    student_query: Optional[str] = None,
    seat_filter: Optional[str] = None,
    event_type_filter: Optional[str] = None
) -> str:
    """Export comprehensive multi-sheet Excel report (.xlsx)."""
    try:
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        df_logs = get_attendance_logs_dataframe(start_date, end_date, student_query, seat_filter, event_type_filter)
        df_summary = get_student_summary_dataframe(start_date, end_date)
        df_students = get_students_master_dataframe()

        with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
            df_summary.to_excel(writer, sheet_name="Attendance Summary", index=False)
            df_logs.to_excel(writer, sheet_name="Detailed Scan Logs", index=False)
            df_students.to_excel(writer, sheet_name="Students Master", index=False)

        return str(filepath)
    except PermissionError:
        raise PermissionError(f"Cannot write to '{filepath.name}'. The file may be open in Excel or another program.")
