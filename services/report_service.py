import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
import pandas as pd
from core.database import get_connection

def get_attendance_logs_dataframe(start_date: Optional[str] = None, end_date: Optional[str] = None, student_query: Optional[str] = None) -> pd.DataFrame:
    """Query raw attendance events and return as pandas DataFrame."""
    conn = get_connection()
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
        sql += " AND (s.full_name LIKE ? OR e.student_id LIKE ? OR e.seat_snapshot LIKE ?)"
        pattern = f"%{student_query}%"
        params.extend([pattern, pattern, pattern])

    sql += " ORDER BY e.event_id DESC"
    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    return df

def get_student_summary_dataframe(start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
    """Calculate aggregated monthly/weekly attendance summary per student."""
    conn = get_connection()
    sql = """
        SELECT 
            e.student_id,
            s.full_name,
            s.assigned_seat,
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
    conn.close()

    if df_events.empty:
        return pd.DataFrame(columns=["Student Name", "Student Token", "Assigned Seat", "Days Present", "Total Scans", "Last Seen"])

    summary_rows = []
    for (std_id, name, seat), group in df_events.groupby(["student_id", "full_name", "assigned_seat"]):
        group["date"] = pd.to_datetime(group["event_timestamp"]).dt.date
        days_present = group["date"].nunique()
        total_scans = len(group)
        last_seen = group["event_timestamp"].max()
        summary_rows.append({
            "Student Name": name,
            "Student Token": std_id,
            "Assigned Seat": seat or "N/A",
            "Days Present": days_present,
            "Total Scans": total_scans,
            "Last Seen": last_seen
        })

    return pd.DataFrame(summary_rows)

def export_attendance_to_csv(filepath: Path, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
    df = get_attendance_logs_dataframe(start_date, end_date)
    df.to_csv(filepath, index=False, encoding="utf-8-sig")
    return str(filepath)

def export_attendance_to_excel(filepath: Path, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
    df_raw = get_attendance_logs_dataframe(start_date, end_date)
    df_summary = get_student_summary_dataframe(start_date, end_date)

    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
        df_summary.to_excel(writer, sheet_name="Monthly Summary", index=False)
        df_raw.to_excel(writer, sheet_name="Raw Scan Events", index=False)

    return str(filepath)
