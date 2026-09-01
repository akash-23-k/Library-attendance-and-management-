import customtkinter as ctk
from services.attendance_service import get_today_metrics, get_recent_scans
from ui.theme import COLOR_PRIMARY, COLOR_SUCCESS, COLOR_WARNING, COLOR_MUTED, COLOR_BG_CARD

class DashboardScreen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.build_ui()

    def build_ui(self):
        # Header Banner
        banner = ctk.CTkFrame(self, fg_color=COLOR_BG_CARD, corner_radius=12, border_width=1, border_color="#334155")
        banner.pack(fill="x", padx=15, pady=(15, 10))

        title_box = ctk.CTkFrame(banner, fg_color="transparent")
        title_box.pack(side="left", padx=20, pady=15)
        
        ctk.CTkLabel(title_box, text="Study Space Attendance Overview", font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(title_box, text="Real-time scan counter, active student presence and study desk allocation.", font=ctk.CTkFont(size=12), text_color=COLOR_MUTED).pack(anchor="w")

        btn_box = ctk.CTkFrame(banner, fg_color="transparent")
        btn_box.pack(side="right", padx=20, pady=15)

        ctk.CTkButton(btn_box, text="📷 Open Scanner", fg_color=COLOR_PRIMARY, font=ctk.CTkFont(weight="bold"), command=lambda: self.app.show_screen("scanner")).pack(side="left", padx=5)
        ctk.CTkButton(btn_box, text="➕ Add Student", fg_color="#334155", hover_color="#475569", command=lambda: self.app.show_screen("students")).pack(side="left", padx=5)

        # KPI Metrics Grid
        metrics_frame = ctk.CTkFrame(self, fg_color="transparent")
        metrics_frame.pack(fill="x", padx=15, pady=5)
        metrics_frame.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="kpi")

        self.kpi_total_lbl = self._create_kpi_card(metrics_frame, 0, "👥 Total Enrolled", "--", "Active Members")
        self.kpi_present_lbl = self._create_kpi_card(metrics_frame, 1, "🟢 Present Now", "--", "Checked-in", text_color=COLOR_SUCCESS)
        self.kpi_occupancy_lbl = self._create_kpi_card(metrics_frame, 2, "🪑 Seat Occupancy", "--", "Capacity Utilized", text_color=COLOR_WARNING)
        self.kpi_scans_lbl = self._create_kpi_card(metrics_frame, 3, "⚡ Scans Today", "--", "Check-in & Check-outs")

        # Bottom Section: Recent Activity Table
        bottom_frame = ctk.CTkFrame(self, fg_color=COLOR_BG_CARD, corner_radius=12, border_width=1, border_color="#334155")
        bottom_frame.pack(fill="both", expand=True, padx=15, pady=(10, 15))

        table_header = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        table_header.pack(fill="x", padx=15, pady=10)
        ctk.CTkLabel(table_header, text="Recent Scan Activity (Today)", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
        ctk.CTkButton(table_header, text="View All Logs →", fg_color="transparent", text_color=COLOR_PRIMARY, width=100, command=lambda: self.app.show_screen("attendance")).pack(side="right")

        self.activity_container = ctk.CTkScrollableFrame(bottom_frame, fg_color="transparent")
        self.activity_container.pack(fill="both", expand=True, padx=10, pady=5)

        self.refresh_data()

    def _create_kpi_card(self, parent, col, title, value, subtext, text_color=None):
        card = ctk.CTkFrame(parent, fg_color=COLOR_BG_CARD, corner_radius=10, border_width=1, border_color="#334155")
        card.grid(row=0, column=col, padx=5, pady=5, sticky="nsew")

        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=12, weight="bold"), text_color=COLOR_MUTED).pack(anchor="w", padx=15, pady=(12, 0))
        val_lbl = ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=24, weight="bold"), text_color=text_color or "#ffffff")
        val_lbl.pack(anchor="w", padx=15, pady=2)
        ctk.CTkLabel(card, text=subtext, font=ctk.CTkFont(size=11), text_color=COLOR_MUTED).pack(anchor="w", padx=15, pady=(0, 12))
        return val_lbl

    def refresh_data(self):
        metrics = get_today_metrics()
        self.kpi_total_lbl.configure(text=str(metrics["total_students"]))
        self.kpi_present_lbl.configure(text=str(metrics["present_count"]))
        self.kpi_occupancy_lbl.configure(text=f"{metrics['occupancy_rate']}%")
        self.kpi_scans_lbl.configure(text=str(metrics["scans_today"]))

        # Clear and repopulate recent scans
        for widget in self.activity_container.winfo_children():
            widget.destroy()

        scans = get_recent_scans(limit=8)
        if not scans:
            ctk.CTkLabel(self.activity_container, text="No attendance scans recorded today yet.", text_color=COLOR_MUTED).pack(pady=20)
            return

        for scan in scans:
            row = ctk.CTkFrame(self.activity_container, fg_color="#0f172a", corner_radius=8, height=40)
            row.pack(fill="x", pady=2, padx=5)

            ctk.CTkLabel(row, text=scan["event_timestamp"].split(" ")[-1], width=80, font=ctk.CTkFont(family="Courier", size=11), text_color=COLOR_MUTED).pack(side="left", padx=8)
            ctk.CTkLabel(row, text=scan["full_name"] or "Unknown", font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(side="left", padx=10, fill="x", expand=True)
            ctk.CTkLabel(row, text=f"Seat {scan['seat_snapshot']}", font=ctk.CTkFont(family="Courier", size=11), text_color="#818cf8", width=90).pack(side="left", padx=5)
            
            badge_color = COLOR_SUCCESS if scan["event_type"] == "CHECK_IN" else COLOR_WARNING
            badge = ctk.CTkLabel(row, text=f" {scan['event_type']} ", fg_color=badge_color, text_color="#000000", font=ctk.CTkFont(size=10, weight="bold"), corner_radius=4)
            badge.pack(side="right", padx=10)
