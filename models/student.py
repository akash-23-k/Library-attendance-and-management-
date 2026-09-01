from dataclasses import dataclass
from typing import Optional

@dataclass
class Admin:
    admin_id: Optional[int]
    username: str
    password_hash: str
    status: str = 'ACTIVE'
    created_at: Optional[str] = None

@dataclass
class Student:
    student_id: str
    full_name: str
    phone: Optional[str] = None
    joining_date: Optional[str] = None
    assigned_seat: Optional[str] = None
    status: str = 'ACTIVE'
    notes: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

@dataclass
class Seat:
    seat_id: int
    seat_number: str
    zone: str
    status: str = 'AVAILABLE'
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

@dataclass
class AttendanceEvent:
    event_id: Optional[int]
    student_id: str
    seat_snapshot: Optional[str]
    event_type: str  # 'CHECK_IN' or 'CHECK_OUT'
    event_timestamp: Optional[str] = None
    device_id: str = 'Local-Station-1'
    remarks: Optional[str] = None
