import customtkinter as ctk
from services.attendance_service import get_seat_occupancy_map
from ui.theme import COLOR_PRIMARY, COLOR_SUCCESS, COLOR_BG_CARD, COLOR_MUTED

class SeatScreen(ctk.CTkFrame):
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
        ctk.CTkLabel(title_box, text="🪑 Study Space Seat Matrix & Desk Allocation", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(title_box, text="Visual occupancy map of Zone A (Main Hall) and Zone B (Silent Cabins).", font=ctk.CTkFont(size=12), text_color=COLOR_MUTED).pack(anchor="w")

        legend = ctk.CTkFrame(top, fg_color="transparent")
        legend.pack(side="right", padx=15, pady=10)

        self._add_legend_item(legend, "● Present (In Study)", COLOR_SUCCESS)
        self._add_legend_item(legend, "● Assigned (Away)", "#818cf8")
        self._add_legend_item(legend, "● Vacant", "#64748b")

        # Scrollable Grid Area
        self.scroll_area = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_area.pack(fill="both", expand=True, padx=15, pady=(5, 15))

        self.refresh_grid()

    def _add_legend_item(self, parent, text, color):
        lbl = ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(size=11, weight="bold"), text_color=color)
        lbl.pack(side="left", padx=6)

    def refresh_grid(self):
        for w in self.scroll_area.winfo_children():
            w.destroy()

        seat_map = get_seat_occupancy_map()

        # Zone A Section
        zone_a_card = ctk.CTkFrame(self.scroll_area, fg_color=COLOR_BG_CARD, corner_radius=12, border_width=1, border_color="#334155")
        zone_a_card.pack(fill="x", pady=6)
        ctk.CTkLabel(zone_a_card, text="ZONE A — MAIN READING HALL (A-01 to A-24)", font=ctk.CTkFont(size=13, weight="bold"), text_color="#c7d2fe").pack(anchor="w", padx=15, pady=(12, 6))

        grid_a = ctk.CTkFrame(zone_a_card, fg_color="transparent")
        grid_a.pack(fill="x", padx=10, pady=(0, 12))
        for col in range(8):
            grid_a.grid_columnconfigure(col, weight=1, uniform="seat")

        # Zone B Section
        zone_b_card = ctk.CTkFrame(self.scroll_area, fg_color=COLOR_BG_CARD, corner_radius=12, border_width=1, border_color="#334155")
        zone_b_card.pack(fill="x", pady=6)
        ctk.CTkLabel(zone_b_card, text="ZONE B — SILENT CABIN DESKS (B-01 to B-24)", font=ctk.CTkFont(size=13, weight="bold"), text_color="#c7d2fe").pack(anchor="w", padx=15, pady=(12, 6))

        grid_b = ctk.CTkFrame(zone_b_card, fg_color="transparent")
        grid_b.pack(fill="x", padx=10, pady=(0, 12))
        for col in range(8):
            grid_b.grid_columnconfigure(col, weight=1, uniform="seat")

        # Populate Seats
        for i in range(1, 25):
            seat_code_a = f"A-{i:02d}"
            seat_data_a = seat_map.get(seat_code_a, {"status": "VACANT", "student": None})
            r, c = (i - 1) // 8, (i - 1) % 8
            self._render_seat_box(grid_a, r, c, seat_code_a, seat_data_a)

            seat_code_b = f"B-{i:02d}"
            seat_data_b = seat_map.get(seat_code_b, {"status": "VACANT", "student": None})
            self._render_seat_box(grid_b, r, c, seat_code_b, seat_data_b)

    def _render_seat_box(self, parent, row, col, seat_code, data):
        st = data["status"]
        if st in ("PRESENT", "OCCUPIED"):
            bg = "#064e3b"
            border = COLOR_SUCCESS
            badge_txt = "IN STUDY"
            badge_color = COLOR_SUCCESS
        elif st == "AWAY":
            bg = "#1e1b4b"
            border = "#6366f1"
            badge_txt = "AWAY"
            badge_color = "#818cf8"
        else:
            bg = "#0f172a"
            border = "#334155"
            badge_txt = "VACANT"
            badge_color = "#64748b"

        box = ctk.CTkFrame(parent, fg_color=bg, border_width=1, border_color=border, corner_radius=8, height=65)
        box.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")

        ctk.CTkLabel(box, text=seat_code, font=ctk.CTkFont(family="Courier", size=11, weight="bold")).pack(pady=(4, 0))
        
        name_txt = data["student"]["full_name"] if data["student"] else "--"
        ctk.CTkLabel(box, text=name_txt, font=ctk.CTkFont(size=10, weight="bold" if data["student"] else "normal"), text_color="#ffffff" if data["student"] else "#64748b").pack()
        
        ctk.CTkLabel(box, text=badge_txt, font=ctk.CTkFont(size=9, weight="bold"), text_color=badge_color).pack(pady=(0, 4))
