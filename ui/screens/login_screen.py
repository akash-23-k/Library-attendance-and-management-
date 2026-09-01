import customtkinter as ctk
from services.auth_service import authenticate_admin
from ui.theme import COLOR_PRIMARY, COLOR_BG_CARD, COLOR_DANGER, COLOR_MUTED

class LoginScreen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.build_ui()

    def build_ui(self):
        # Center container
        center_card = ctk.CTkFrame(self, width=420, fg_color=COLOR_BG_CARD, corner_radius=16, border_width=1, border_color="#334155")
        center_card.place(relx=0.5, rely=0.5, anchor="center")

        # Branding Header
        icon_lbl = ctk.CTkLabel(center_card, text="📚", font=ctk.CTkFont(size=36))
        icon_lbl.pack(pady=(25, 4))

        title_lbl = ctk.CTkLabel(center_card, text="StudySpace Manager", font=ctk.CTkFont(size=20, weight="bold"))
        title_lbl.pack()

        sub_lbl = ctk.CTkLabel(center_card, text="Local Library Attendance & Study-Space System", font=ctk.CTkFont(size=12), text_color=COLOR_MUTED)
        sub_lbl.pack(pady=(0, 20))

        # Form Inputs
        form_box = ctk.CTkFrame(center_card, fg_color="transparent")
        form_box.pack(fill="x", padx=35, pady=5)

        ctk.CTkLabel(form_box, text="Username", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(0, 4))
        self.user_entry = ctk.CTkEntry(form_box, placeholder_text="Enter username", height=38)
        self.user_entry.pack(fill="x", pady=(0, 12))
        self.user_entry.insert(0, "admin")

        ctk.CTkLabel(form_box, text="Password", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(0, 4))
        self.pass_entry = ctk.CTkEntry(form_box, placeholder_text="Enter password", show="•", height=38)
        self.pass_entry.pack(fill="x", pady=(0, 10))
        self.pass_entry.bind("<Return>", lambda e: self.do_login())

        self.err_lbl = ctk.CTkLabel(form_box, text="", font=ctk.CTkFont(size=11), text_color=COLOR_DANGER)
        self.err_lbl.pack(pady=(0, 10))

        self.login_btn = ctk.CTkButton(
            form_box, 
            text="Sign In to Library Station", 
            fg_color=COLOR_PRIMARY, 
            hover_color="#4338ca", 
            font=ctk.CTkFont(size=13, weight="bold"), 
            height=40,
            command=self.do_login
        )
        self.login_btn.pack(fill="x", pady=(0, 15))

        # First-run tip
        tip_box = ctk.CTkFrame(center_card, fg_color="#0f172a", corner_radius=8)
        tip_box.pack(fill="x", padx=35, pady=(0, 25))
        ctk.CTkLabel(tip_box, text="💡 Offline Local Access\nDefault login: admin / admin123", font=ctk.CTkFont(size=10), text_color=COLOR_MUTED).pack(pady=8)

    def do_login(self):
        username = self.user_entry.get().strip()
        password = self.pass_entry.get()

        if not username or not password:
            self.err_lbl.configure(text="Please enter both username and password.")
            return

        admin = authenticate_admin(username, password)
        if admin:
            self.err_lbl.configure(text="")
            self.pass_entry.delete(0, "end")
            self.app.on_login_success(admin)
        else:
            self.err_lbl.configure(text="Invalid username or password.")
