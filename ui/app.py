import datetime
from typing import Optional, Dict, Any
import customtkinter as ctk
from core.config import APP_NAME, APP_VERSION, DEFAULT_LIBRARY_NAME
from ui.theme import apply_app_theme, COLOR_PRIMARY, COLOR_BG_DARK, COLOR_BG_CARD, COLOR_MUTED
from ui.screens.login_screen import LoginScreen
from ui.screens.dashboard_screen import DashboardScreen
from ui.screens.scanner_screen import ScannerScreen
from ui.screens.student_screen import StudentScreen
from ui.screens.seat_screen import SeatScreen
from ui.screens.attendance_screen import AttendanceScreen
from ui.screens.report_screen import ReportScreen
from ui.screens.settings_screen import SettingsScreen

class StudySpaceApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        apply_app_theme()

        self.title(f"{APP_NAME} - {DEFAULT_LIBRARY_NAME}")
        self.geometry("1180x740")
        self.minsize(980, 640)

        self.current_user: Optional[Dict[str, Any]] = None
        self.screens = {}
        self.current_screen_name = "login"

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Main Container
        self.main_container = ctk.CTkFrame(self, fg_color=COLOR_BG_DARK, corner_radius=0)
        self.main_container.pack(fill="both", expand=True)

        # Build Login Screen initially
        self.login_screen = LoginScreen(self.main_container, self)
        self.login_screen.pack(fill="both", expand=True)

    def on_login_success(self, admin_dict: Dict[str, Any]):
        """Callback invoked when admin credentials are authenticated."""
        self.current_user = admin_dict
        self.login_screen.pack_forget()
        self.build_app_shell()
        self.show_screen("dashboard")
        self.update_clock()

    def logout(self):
        """Log out current admin user and lock app."""
        if "scanner" in self.screens:
            self.screens["scanner"].stop_camera()

        self.current_user = None
        for w in self.main_container.winfo_children():
            w.pack_forget()

        self.login_screen.pack(fill="both", expand=True)
        self.current_screen_name = "login"

    def build_app_shell(self):
        # Clear main container
        for w in self.main_container.winfo_children():
            w.destroy()

        # 1. Top Header Bar
        self.header = ctk.CTkFrame(self.main_container, height=55, fg_color=COLOR_BG_CARD, corner_radius=0, border_width=1, border_color="#334155")
        self.header.pack(fill="x", side="top")

        brand_box = ctk.CTkFrame(self.header, fg_color="transparent")
        brand_box.pack(side="left", padx=15, pady=8)
        
        logo = ctk.CTkLabel(brand_box, text="📚", font=ctk.CTkFont(size=20))
        logo.pack(side="left", padx=(0, 8))

        brand_text = ctk.CTkFrame(brand_box, fg_color="transparent")
        brand_text.pack(side="left")
        ctk.CTkLabel(brand_text, text=APP_NAME, font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(brand_text, text=f"Offline MVP {APP_VERSION}", font=ctk.CTkFont(size=10), text_color="#10b981").pack(anchor="w")

        # Top Right Meta & Logout
        meta_box = ctk.CTkFrame(self.header, fg_color="transparent")
        meta_box.pack(side="right", padx=15, pady=8)

        ctk.CTkButton(meta_box, text="Logout", width=65, height=28, fg_color="#334155", hover_color="#475569", font=ctk.CTkFont(size=11), command=self.logout).pack(side="right", padx=(8, 0))

        self.clock_lbl = ctk.CTkLabel(meta_box, text="--:--:--", font=ctk.CTkFont(family="Courier", size=13, weight="bold"), text_color="#c7d2fe")
        self.clock_lbl.pack(side="right", padx=10)

        user_name = self.current_user["username"] if self.current_user else "Admin"
        user_badge = ctk.CTkLabel(meta_box, text=f"👤 {user_name}", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLOR_MUTED)
        user_badge.pack(side="right", padx=10)

        # 2. Body Container (Sidebar + Screens)
        self.body = ctk.CTkFrame(self.main_container, fg_color=COLOR_BG_DARK, corner_radius=0)
        self.body.pack(fill="both", expand=True)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self.body, width=210, fg_color=COLOR_BG_CARD, corner_radius=0, border_width=1, border_color="#334155")
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.nav_buttons = {}
        nav_items = [
            ("dashboard", "📊 Dashboard"),
            ("scanner", "📷 QR Scanner"),
            ("students", "🎓 Students & QR"),
            ("seats", "🪑 Seat Matrix"),
            ("attendance", "📋 Attendance Log"),
            ("reports", "📈 Reports & Export"),
            ("settings", "⚙️ Settings & Backup")
        ]

        ctk.CTkLabel(self.sidebar, text="NAVIGATION", font=ctk.CTkFont(size=10, weight="bold"), text_color=COLOR_MUTED).pack(anchor="w", padx=15, pady=(15, 6))

        for key, label in nav_items:
            btn = ctk.CTkButton(
                self.sidebar,
                text=label,
                anchor="w",
                height=38,
                corner_radius=8,
                fg_color="transparent",
                text_color="#e2e8f0",
                hover_color="#334155",
                font=ctk.CTkFont(size=12, weight="bold"),
                command=lambda k=key: self.show_screen(k)
            )
            btn.pack(fill="x", padx=10, pady=2)
            self.nav_buttons[key] = btn

        # Content Screen Container
        self.content_area = ctk.CTkFrame(self.body, fg_color="transparent")
        self.content_area.pack(side="right", fill="both", expand=True)

        # Initialize Screens
        self.screens = {
            "dashboard": DashboardScreen(self.content_area, self),
            "scanner": ScannerScreen(self.content_area, self),
            "students": StudentScreen(self.content_area, self),
            "seats": SeatScreen(self.content_area, self),
            "attendance": AttendanceScreen(self.content_area, self),
            "reports": ReportScreen(self.content_area, self),
            "settings": SettingsScreen(self.content_area, self)
        }

    def show_screen(self, screen_name: str):
        if self.current_screen_name == "scanner" and screen_name != "scanner":
            if "scanner" in self.screens:
                self.screens["scanner"].stop_camera()

        for name, screen in self.screens.items():
            screen.pack_forget()

        for k, btn in self.nav_buttons.items():
            if k == screen_name:
                btn.configure(fg_color=COLOR_PRIMARY, text_color="#ffffff")
            else:
                btn.configure(fg_color="transparent", text_color="#e2e8f0")

        if screen_name in self.screens:
            self.screens[screen_name].pack(fill="both", expand=True)
            self.current_screen_name = screen_name

            if screen_name == "scanner":
                self.screens["scanner"].start_camera()
            elif screen_name == "dashboard":
                self.screens["dashboard"].refresh_data()
            elif screen_name == "seats":
                self.screens["seats"].refresh_grid()
            elif screen_name == "students":
                self.screens["students"].refresh_table()

    def update_clock(self):
        if hasattr(self, "clock_lbl") and self.clock_lbl.winfo_exists():
            now_str = datetime.datetime.now().strftime("%I:%M:%S %p")
            self.clock_lbl.configure(text=now_str)
            self.after(1000, self.update_clock)

    def on_close(self):
        try:
            if "scanner" in self.screens:
                self.screens["scanner"].stop_camera()
        except Exception:
            pass
        self.destroy()
