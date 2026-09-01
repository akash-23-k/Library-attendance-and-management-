# StudySpace Manager — Local Library Attendance System

An offline-first desktop attendance and study-space management system built for local study libraries based on **PRD v1.0**.

---

## 🎨 Interactive Figma / UI Prototype
Open the interactive UI preview directly in your browser or preview pane:
👉 **[Open UI Prototype (HTML)](../.gemini/antigravity/brain/7a9334fd-efc3-406f-b767-61bb848c345a/ui_prototype.html)**

---

## 🚀 Quickstart

### 1. Requirements
- Windows 10/11
- Python 3.11+
- Standard USB Webcam / Laptop Camera

### 2. Run Desktop App
```bash
python main.py
```

### 3. Run Automated Tests
```bash
python -m unittest tests/test_all.py
```

---

## 🌟 Key Features (MVP v1.0)
1. **Live Webcam QR Scanner**: Real-time detection with zero internet requirements.
2. **Student & Desk Matrix**: Register students, assign study seats (Zone A / Zone B), and avoid double-booking.
3. **Printable QR Cards**: High-res student passes with library branding, student details, and QR token.
4. **Attendance Logging & Policy**: Instant check-in/check-out toggle with 60-second duplicate scan cooldown.
5. **Excel & CSV Export**: One-click export to multi-sheet `.xlsx` workbooks and `.csv` logs.
6. **SQLite Online Backup & Restore**: Safe database backup rotation with automatic rollback safety snapshots.
