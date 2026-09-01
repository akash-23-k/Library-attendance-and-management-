import customtkinter as ctk
from services.report_service import get_attendance_logs_dataframe
from ui.theme import COLOR_PRIMARY, COLOR_SUCCESS, COLOR_WARNING, COLOR_BG_CARD, COLOR_MUTED

class AttendanceScreen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.build_ui()

    def build_ui(self):
        # Header
        top = ctk.CTkFrame(self, fg_color=COLOR_BG_CARD, corner_radius=10, border_width=1, border_color="#334155")
        top.pack(fill="x", padx=15, pady=(15, 10))

        title_box = ctk.CTkFrame(top, fg_color="transparent")
        title_box.pack(side="left", padx=15, pady=10)
        ctk.CTkLabel(title_box, text="📋 Attendance Audit Logs", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(title_box, text="Immutable timestamped record of every entry and exit event with seat snapshot.", font=ctk.CTkFont(size=12), text_color=COLOR_MUTED).pack(anchor="w")

        # Filters
        filter_bar = ctk.CTkFrame(self, fg_color=COLOR_BG_CARD, corner_radius=8, border_width=1, border_color="#334155")
        filter_bar.pack(fill="x", padx=15, pady=5)

        self.search_entry = ctk.CTkEntry(filter_bar, placeholder_text="🔍 Filter by student name, token or seat...", width=300)
        self.search_entry.pack(side="left", padx=12, pady=8)
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh_logs())

        ctk.CTkButton(filter_bar, text="Refresh Logs", width=100, fg_color="#334155", command=self.refresh_logs).pack(side="right", padx=12)

        # Table Container
        table_card = ctk.CTkFrame(self, fg_color=COLOR_BG_CARD, corner_radius=12, border_width=1, border_color="#334155")
        table_card.pack(fill="both", expand=True, padx=15, pady=(5, 15))

        th = ctk.CTkFrame(table_card, fg_color="#0f172a", corner_radius=6, height=35)
        th.pack(fill="x", padx=8, pady=(8, 4))
        ctk.CTkLabel(th, text="EVENT ID", width=70, font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_MUTED).pack(side="left", padx=5)
        ctk.CTkLabel(th, text="TIMESTAMP", width=140, font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_MUTED).pack(side="left", padx=5)
        ctk.CTkLabel(th, text="TOKEN", width=110, font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_MUTED).pack(side="left", padx=5)
        ctk.CTkLabel(th, text="STUDENT NAME", width=180, font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_MUTED, anchor="w").pack(side="left", padx=5)
        ctk.CTkLabel(th, text="SEAT SNAPSHOT", width=110, font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_MUTED).pack(side="left", padx=5)
        ctk.CTkLabel(th, text="EVENT", width=100, font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_MUTED).pack(side="right", padx=15)

        self.table_body = ctk.CTkScrollableFrame(table_card, fg_color="transparent")
        self.table_body.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self.refresh_logs()

    def refresh_logs(self):
        for w in self.table_body.winfo_children():
            w.destroy()

        q = self.search_entry.get().strip()
        df = get_attendance_logs_dataframe(student_query=q if q else None)

        if df.empty:
            ctk.CTkLabel(self.table_body, text="No attendance events found.", text_color=COLOR_MUTED).pack(pady=30)
            return

        for _, row in df.iterrows():
            r_frame = ctk.CTkFrame(self.table_body, fg_color="#0f172a", corner_radius=8, height=40)
            r_frame.pack(fill="x", pady=2, padx=2)

            ctk.CTkLabel(r_frame, text=f"#{row['Event ID']}", width=70, font=ctk.CTkFont(family="Courier", size=11), text_color=COLOR_MUTED).pack(side="left", padx=5)
            ctk.CTkLabel(r_frame, text=str(row["Timestamp"]), width=140, font=ctk.CTkFont(family="Courier", size=11)).pack(side="left", padx=5)
            ctk.CTkLabel(r_frame, text=str(row["Student Token"]), width=110, font=ctk.CTkFont(family="Courier", size=11, weight="bold"), text_color="#818cf8").pack(side="left", padx=5)
            ctk.CTkLabel(r_frame, text=str(row["Student Name"] or "Unknown"), width=180, font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(r_frame, text=f"Seat {row['Seat Snapshot']}", width=110, font=ctk.CTkFont(family="Courier", size=11), text_color="#c7d2fe").pack(side="left", padx=5)

            badge_color = COLOR_SUCCESS if row["Event Type"] == "CHECK_IN" else COLOR_WARNING
            badge = ctk.CTkLabel(r_frame, text=f" {row['Event Type']} ", fg_color=badge_color, text_color="#000000", font=ctk.CTkFont(size=10, weight="bold"), corner_radius=4)
            badge.pack(side="right", padx=15)
