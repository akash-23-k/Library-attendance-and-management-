import customtkinter as ctk
from PIL import Image, ImageTk
from services.scanner_service import CameraScannerService
from services.attendance_service import record_scan_event
from ui.theme import COLOR_PRIMARY, COLOR_SUCCESS, COLOR_WARNING, COLOR_DANGER, COLOR_BG_CARD, COLOR_MUTED

class ScannerScreen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.scanner = CameraScannerService()
        self.build_ui()

    def build_ui(self):
        # Header
        top_bar = ctk.CTkFrame(self, fg_color=COLOR_BG_CARD, corner_radius=10, border_width=1, border_color="#334155")
        top_bar.pack(fill="x", padx=15, pady=(15, 10))
        
        ctk.CTkLabel(top_bar, text="📷 Live Attendance Scanner Station", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=15, pady=10)
        
        self.cam_status_lbl = ctk.CTkLabel(top_bar, text="● Camera: Initializing...", text_color=COLOR_WARNING, font=ctk.CTkFont(size=11, weight="bold"))
        self.cam_status_lbl.pack(side="right", padx=15)

        # Content 2-Column Split
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=15, pady=5)
        content.grid_columnconfigure(0, weight=6)
        content.grid_columnconfigure(1, weight=4)
        content.grid_rowconfigure(0, weight=1)

        # Left Column: Video Viewfinder & Simulator Bar
        left_col = ctk.CTkFrame(content, fg_color=COLOR_BG_CARD, corner_radius=12, border_width=1, border_color="#334155")
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=5)

        # Video Canvas / Label
        self.video_lbl = ctk.CTkLabel(left_col, text="Webcam Feed Loading...\n(Align student QR pass inside camera)", fg_color="#090d16", corner_radius=8)
        self.video_lbl.pack(fill="both", expand=True, padx=12, pady=12)

        # Bottom Quick Test / Scanner Bar
        sim_bar = ctk.CTkFrame(left_col, fg_color="#0f172a", corner_radius=8)
        sim_bar.pack(fill="x", padx=12, pady=(0, 12))

        ctk.CTkLabel(sim_bar, text="🧪 Quick Scan Trigger / Barcode Input:", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_MUTED).pack(anchor="w", padx=10, pady=(6, 2))
        
        input_row = ctk.CTkFrame(sim_bar, fg_color="transparent")
        input_row.pack(fill="x", padx=10, pady=(0, 8))

        self.qr_input = ctk.CTkEntry(input_row, placeholder_text="Enter or scan QR token (e.g. LIB-8F4K2M)...", font=ctk.CTkFont(family="Courier", size=12))
        self.qr_input.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.qr_input.bind("<Return>", lambda e: self.process_scanned_token(self.qr_input.get()))

        ctk.CTkButton(input_row, text="Submit Scan", width=110, fg_color=COLOR_PRIMARY, command=lambda: self.process_scanned_token(self.qr_input.get())).pack(side="right")

        # Quick sample tokens
        sample_row = ctk.CTkFrame(sim_bar, fg_color="transparent")
        sample_row.pack(fill="x", padx=10, pady=(0, 8))

        ctk.CTkButton(sample_row, text="Rahul (A-12)", width=90, height=24, font=ctk.CTkFont(size=10), fg_color="#334155", command=lambda: self.process_scanned_token("LIB-8F4K2M")).pack(side="left", padx=2)
        ctk.CTkButton(sample_row, text="Priya (A-04)", width=90, height=24, font=ctk.CTkFont(size=10), fg_color="#334155", command=lambda: self.process_scanned_token("LIB-9G3M1P")).pack(side="left", padx=2)
        ctk.CTkButton(sample_row, text="Amit (B-02)", width=90, height=24, font=ctk.CTkFont(size=10), fg_color="#334155", command=lambda: self.process_scanned_token("LIB-2D8R5W")).pack(side="left", padx=2)
        ctk.CTkButton(sample_row, text="Test Invalid", width=90, height=24, font=ctk.CTkFont(size=10), fg_color="#7f1d1d", command=lambda: self.process_scanned_token("LIB-INVALID-99")).pack(side="left", padx=2)

        # Right Column: Instant Scan Feedback Card
        right_col = ctk.CTkFrame(content, fg_color=COLOR_BG_CARD, corner_radius=12, border_width=1, border_color="#334155")
        right_col.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=5)

        self.res_card = ctk.CTkFrame(right_col, fg_color="#064e3b", corner_radius=10, border_width=2, border_color=COLOR_SUCCESS)
        self.res_card.pack(fill="x", padx=15, pady=15)

        self.res_icon = ctk.CTkLabel(self.res_card, text="✓", font=ctk.CTkFont(size=32, weight="bold"), text_color=COLOR_SUCCESS)
        self.res_icon.pack(pady=(12, 0))

        self.res_title = ctk.CTkLabel(self.res_card, text="READY TO SCAN", font=ctk.CTkFont(size=16, weight="bold"), text_color="#ffffff")
        self.res_title.pack()

        self.res_msg = ctk.CTkLabel(self.res_card, text="Hold student QR pass steadily in camera view", font=ctk.CTkFont(size=11), text_color=COLOR_MUTED)
        self.res_msg.pack(pady=(0, 10))

        # Details box
        self.detail_box = ctk.CTkFrame(self.res_card, fg_color="#0f172a", corner_radius=8)
        self.detail_box.pack(fill="x", padx=12, pady=(0, 12))

        self.det_name = ctk.CTkLabel(self.detail_box, text="Student: --", font=ctk.CTkFont(size=13, weight="bold"), anchor="w")
        self.det_name.pack(fill="x", padx=10, pady=(6, 2))

        self.det_seat = ctk.CTkLabel(self.detail_box, text="Desk: --", font=ctk.CTkFont(size=12), text_color="#818cf8", anchor="w")
        self.det_seat.pack(fill="x", padx=10, pady=2)

        self.det_time = ctk.CTkLabel(self.detail_box, text="Timestamp: --", font=ctk.CTkFont(family="Courier", size=11), text_color=COLOR_MUTED, anchor="w")
        self.det_time.pack(fill="x", padx=10, pady=(2, 6))

        # Instructions / Policy note
        info_card = ctk.CTkFrame(right_col, fg_color="#0f172a", corner_radius=10)
        info_card.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        ctk.CTkLabel(info_card, text="Operational Guidelines", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=12, pady=(10, 4))
        policy_text = (
            "• 1st Scan of day = Check-In (Occupies Desk)\n"
            "• 2nd Scan of day = Check-Out (Marks Away)\n"
            "• Duplicate scans within 60s cooldown are ignored\n"
            "• Zero Internet Required (Saves to local SQLite)\n"
            "• High contrast ID pass recommended for best scan speed"
        )
        ctk.CTkLabel(info_card, text=policy_text, font=ctk.CTkFont(size=11), text_color=COLOR_MUTED, justify="left").pack(anchor="w", padx=12, pady=4)

    def start_camera(self):
        self.scanner.start(
            frame_callback=self.on_frame,
            qr_callback=self.on_qr_detected,
            status_callback=self.on_scanner_status
        )

    def stop_camera(self):
        self.scanner.stop()

    def on_frame(self, pil_image: Image.Image):
        # Resize to fit frame
        img_resized = pil_image.resize((520, 390))
        ctk_img = ctk.CTkImage(light_image=img_resized, dark_image=img_resized, size=(520, 390))
        self.video_lbl.configure(image=ctk_img, text="")

    def on_scanner_status(self, status: str):
        if status == "RUNNING":
            self.cam_status_lbl.configure(text="● Camera: Live (USB HD)", text_color=COLOR_SUCCESS)
        elif status == "NO_CAMERA":
            self.cam_status_lbl.configure(text="⚠️ Camera: Not detected (Use Simulator)", text_color=COLOR_WARNING)
        else:
            self.cam_status_lbl.configure(text=f"⚠️ Camera: {status}", text_color=COLOR_DANGER)

    def on_qr_detected(self, token: str):
        # Schedule in main UI thread
        self.after(0, lambda: self.process_scanned_token(token))

    def process_scanned_token(self, token: str):
        if not token or not token.strip():
            return

        res = record_scan_event(token.strip())
        self.qr_input.delete(0, "end")

        if res["status"] == "SUCCESS":
            self.res_card.configure(fg_color="#064e3b", border_color=COLOR_SUCCESS)
            self.res_icon.configure(text="✓", text_color=COLOR_SUCCESS)
            self.res_title.configure(text=f"{res['event_type']} SUCCESSFUL")
            self.res_msg.configure(text="Attendance verified and recorded in SQLite.")
            
            std = res["student"]
            self.det_name.configure(text=f"Student: {std['full_name']} ({std['student_id']})")
            self.det_seat.configure(text=f"Assigned Desk: {res['seat']}")
            self.det_time.configure(text=f"Timestamp: {res['timestamp']}")
        elif res["status"] == "DUPLICATE":
            self.res_card.configure(fg_color="#78350f", border_color=COLOR_WARNING)
            self.res_icon.configure(text="⏳", text_color=COLOR_WARNING)
            self.res_title.configure(text="DUPLICATE SCAN IGNORED")
            self.res_msg.configure(text=res["message"])
        else:
            self.res_card.configure(fg_color="#7f1d1d", border_color=COLOR_DANGER)
            self.res_icon.configure(text="✕", text_color=COLOR_DANGER)
            self.res_title.configure(text="STUDENT NOT RECOGNIZED")
            self.res_msg.configure(text=res["message"])
            self.det_name.configure(text=f"Token: {token}")
            self.det_seat.configure(text="Desk: N/A")
            self.det_time.configure(text="Timestamp: Now")

        # Refresh dashboard data
        self.app.screens["dashboard"].refresh_data()
