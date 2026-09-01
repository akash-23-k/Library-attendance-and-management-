# StudySpace Manager — Local Library Attendance & Study-Space System

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Architecture](https://img.shields.io/badge/architecture-offline--first-emerald.svg)]()
[![Database](https://img.shields.io/badge/storage-SQLite3%20WAL-indigo.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)]()

**StudySpace Manager** is a cost-effective, offline-first desktop attendance and study-desk allocation system designed specifically for local study libraries and reading halls. It turns an ordinary Windows PC/laptop and a standard USB webcam into a complete digital attendance station—eliminating manual registers, paper logs, and costly biometric subscriptions.

Built in accordance with **PRD v1.0 (Offline-First MVP)**.

---

## 🎨 Interactive UI Prototype (Figma-Grade)

An interactive, high-fidelity UI prototype of the entire system is included directly in this repository:
- **File:** `ui_prototype.html`
- **How to view:** Double-click or open `ui_prototype.html` in any modern web browser (Edge, Chrome, Firefox) to explore all interactive screens, test scans, seat matrix layouts, and report exports.

---

## 🌟 Key Features

1. **📷 Live Webcam QR Scanner:**
   - Real-time continuous QR code detection via OpenCV.
   - Immediate visual feedback on scan (Student Name, Allocated Seat, Check-In / Check-Out, Timestamp).
   - Zero internet dependency—scans are validated and saved directly into the local SQLite database.

2. **⚡ Two-Level Duplicate Scan Protection:**
   - **Level 1 (In-Memory):** Rejects rapid consecutive webcam frames.
   - **Level 2 (Database-Level):** Checks last recorded scan timestamp in SQLite to enforce the configurable cooldown interval (default: 60s) even across application restarts.

3. **🎓 Student & Desk Matrix Management:**
   - Register students with contact details, notes, and study seats.
   - Automatic seat synchronization: assigning a seat marks it occupied; deactivating or reassigning releases the old seat atomically.
   - Conflict prevention: double-booking of active study seats is strictly prevented.

4. **📇 High-Resolution Printable QR Passcards:**
   - Generates non-guessable, cryptographically secure student tokens (`LIB-XXXXXX`) using Python's `secrets` module.
   - Privacy-focused: QR payload contains *only* the student token (no phone numbers or personal data embedded).
   - Formats printable 500x680 ID passcards with library branding and seat number ready to print or save.

5. **🪑 2D Visual Seat Layout:**
   - Real-time visual matrix of **Zone A (Main Reading Hall)** and **Zone B (Silent Cabin Desks)**.
   - Clear visual status distinction:
     - 🟢 **Present (In Study):** Student is currently checked in today.
     - 🔵 **Assigned (Away):** Seat allocated, but student is currently checked out.
     - ⚫ **Vacant:** Available for new student assignment.

6. **📈 Reports & Multi-Sheet Excel / CSV Exports:**
   - Daily, weekly, and custom date range attendance logs.
   - One-click export to multi-sheet Microsoft Excel (`.xlsx`) workbooks:
     - Sheet 1: *Attendance Summary* (Days present, check-ins, check-outs, total scans, last seen)
     - Sheet 2: *Detailed Scan Logs* (Full timestamped event audit trail)
     - Sheet 3: *Students Master* (Enrolled student directory)
   - UTF-8 BOM CSV exports for native Windows Excel compatibility.

7. **💾 Automated Database Safety & Rollback Restore:**
   - Thread-safe online backups via SQLite `Connection.backup()` API.
   - Validation check: verifies backup database integrity and schema before restoring.
   - Automatic safety snapshot: creates a pre-restore backup of the live database before applying any restore.

8. **🔐 Local Admin Authentication:**
   - Secure PBKDF2-HMAC-SHA256 password hashing with unique random salt.
   - Login session management with quick logout lock.

---

## 🏗️ Architecture Overview

```
Desktop UI (CustomTkinter)
       │
       ▼
Application / Service Layer (Attendance, Students, QR, Reports, Backup, Auth)
       │
       ▼
Repository / Data Layer (Transactions, Constraints, WAL Mode, Foreign Keys)
       │
       ▼
Local SQLite Database (library_data.db)
```

- **Clean Separation of Concerns:** UI screens never execute direct raw database mutations; all operations pass through dedicated business services.
- **ACID Transaction Safety:** Operations affecting multiple tables (e.g. Student Registration + Seat Status + Audit Log) execute inside atomic `with conn:` transactions with automatic rollback on error.
- **Future Scalability:** Clean service interfaces allow future migration to a remote PostgreSQL/cloud database without rewriting UI or business logic.

---

## 📂 Project Structure

```
.
├── core/
│   ├── __init__.py
│   ├── config.py              # Application settings, paths, and environment helpers
│   └── database.py            # SQLite schema, tables, indexes, and connection factory
├── models/
│   ├── __init__.py
│   └── student.py             # Admin, Student, Seat, and AttendanceEvent dataclasses
├── services/
│   ├── __init__.py
│   ├── auth_service.py        # Admin login, password hashing, and credentials check
│   ├── student_service.py     # Student CRUD, seat assignment synchronization
│   ├── attendance_service.py  # Check-in/out engine, two-level duplicate cooldown
│   ├── qr_service.py          # Secure token generator & printable passcard builder
│   ├── scanner_service.py     # Background OpenCV webcam capture & QR decoder
│   ├── report_service.py      # Pandas & OpenPyXL Excel/CSV export service
│   └── backup_service.py      # SQLite online backup & verified rollback restore
├── ui/
│   ├── __init__.py
│   ├── app.py                 # Main application window & navigation controller
│   ├── theme.py               # CustomTkinter styling palette & typography
│   └── screens/
│       ├── login_screen.py    # Admin sign-in screen
│       ├── dashboard_screen.py# Real-time metrics & recent activity feed
│       ├── scanner_screen.py  # Live camera viewfinder & scan result cards
│       ├── student_screen.py  # Student table, registration modal, QR pass preview
│       ├── seat_screen.py     # 2D Zone A & Zone B interactive seat matrix
│       ├── attendance_screen.py# Filterable timestamped attendance event logs
│       ├── report_screen.py   # Aggregated summary & Excel/CSV export triggers
│       └── settings_screen.py # Library preferences, password change & backup tool
├── data/                      # Local data directory (ignored by git)
│   ├── library_data.db        # SQLite production database
│   ├── qr_cards/              # Generated student ID pass images
│   ├── backups/               # Database backup files
│   └── exports/               # Exported Excel and CSV spreadsheets
├── scripts/
│   └── seed_demo.py           # Demo dataset seeder (for development / testing)
├── tests/
│   ├── __init__.py
│   └── test_all.py            # Comprehensive automated test suite
├── main.py                    # Application entrypoint
├── requirements.txt           # Pinned dependencies
├── ui_prototype.html          # Standalone interactive UI prototype
└── README.md
```

---

## 🚀 Getting Started

### 1. Prerequisites
- **Operating System:** Windows 10 / 11 (or Linux / macOS with Python 3.11+)
- **Python:** Version 3.11, 3.12, or 3.14
- **Hardware:** Standard computer/laptop with USB or integrated webcam

### 2. Installation
Clone the repository and install the dependencies:
```bash
git clone https://github.com/akash-23-k/Library-attendance-and-management-.git
cd Library-attendance-and-management-
pip install -r requirements.txt
```

### 3. (Optional) Seed Demo Data
To populate the database with sample students, assigned seats, and initial scan records:
```bash
python scripts/seed_demo.py
```

### 4. Launch the Desktop Application
```bash
python main.py
```

**Default Admin Credentials:**
- **Username:** `admin`
- **Password:** `admin123`
*(Password can be updated anytime under Settings).*

---

## 🧪 Running Automated Tests

The test suite runs in complete isolation using a temporary database without affecting live library records:

```bash
python -m unittest tests/test_all.py
```
or
```bash
python -m unittest discover tests
```

### Test Coverage Summary:
- **Authentication & Security:** Password hashing, verification, invalid credentials rejection, password updates.
- **Database & Foreign Keys:** Foreign key constraints, transaction rollbacks on integrity violation, index validation.
- **Student Management:** Student creation, ID token generation, validation, seat occupancy sync.
- **Seat Management:** Desk allocation, seat reassignment (freeing old, occupying new), conflict prevention, release on deactivation.
- **Attendance Engine:** Check-In / Check-Out toggle, in-memory duplicate cooldown, database-level cooldown across restarts, inactive student rejection, unregistered QR rejection, historical seat snapshot immutability.
- **Reports & Exports:** Filter queries, multi-sheet Excel generation, CSV generation with UTF-8 BOM.
- **Backup & Recovery:** Backup generation, corrupted backup rejection, safe restoration with rollback snapshot.

---

## 📦 PyInstaller Packaging (Windows .EXE)

To bundle the application into a standalone Windows executable:
```bash
pip install pyinstaller
pyinstaller --noconsole --name "StudySpaceManager" --add-data "core;core" --add-data "services;services" --add-data "ui;ui" --add-data "models;models" main.py
```

---

## 🔒 Privacy & Data Minimization
- **QR Codes:** QR codes store only the opaque student token (e.g. `LIB-8F4K2M`). No student names, phone numbers, or addresses are encoded in QR payloads.
- **Offline Storage:** All student records, timestamps, and pass images remain 100% local on the library computer. No external telemetry or cloud transmission is performed.
- **Version Control Safety:** Database `.db` files, backup snapshots, and student pass images are excluded by `.gitignore`.

---

## 🗺️ Future Roadmap
- **Phase 1 (Current):** Offline-first desktop MVP, SQLite, webcam QR attendance, Excel/CSV export, local backup.
- **Phase 2:** Multi-operator staff accounts with role-based permissions, automated daily backup scheduler, customizable seat layout editor.
- **Phase 3:** Optional encrypted cloud synchronization for remote owner dashboards across multiple library branches.
