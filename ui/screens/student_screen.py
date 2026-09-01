import customtkinter as ctk
from PIL import Image
from services.student_service import list_students, create_student, toggle_student_status, get_available_seats
from services.qr_service import generate_student_id_card
from ui.theme import COLOR_PRIMARY, COLOR_SUCCESS, COLOR_WARNING, COLOR_DANGER, COLOR_BG_CARD, COLOR_MUTED

class StudentScreen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.build_ui()

    def build_ui(self):
        # Top Header
        top = ctk.CTkFrame(self, fg_color=COLOR_BG_CARD, corner_radius=10, border_width=1, border_color="#334155")
        top.pack(fill="x", padx=15, pady=(15, 10))

        title_box = ctk.CTkFrame(top, fg_color="transparent")
        title_box.pack(side="left", padx=15, pady=10)
        ctk.CTkLabel(title_box, text="🎓 Student Directory & QR Passcards", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(title_box, text="Manage library memberships, permanent desk allocations and printable QR cards.", font=ctk.CTkFont(size=12), text_color=COLOR_MUTED).pack(anchor="w")

        ctk.CTkButton(top, text="➕ Register New Student", fg_color=COLOR_PRIMARY, font=ctk.CTkFont(weight="bold"), command=self.open_add_modal).pack(side="right", padx=15, pady=10)

        # Filter & Search bar
        search_bar = ctk.CTkFrame(self, fg_color=COLOR_BG_CARD, corner_radius=8, border_width=1, border_color="#334155")
        search_bar.pack(fill="x", padx=15, pady=5)

        self.search_entry = ctk.CTkEntry(search_bar, placeholder_text="🔍 Search by name, student ID, contact or seat...", width=320)
        self.search_entry.pack(side="left", padx=12, pady=8)
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh_table())

        self.status_filter = ctk.CTkOptionMenu(search_bar, values=["ALL", "ACTIVE", "INACTIVE"], command=lambda v: self.refresh_table(), width=130)
        self.status_filter.pack(side="left", padx=5)

        ctk.CTkButton(search_bar, text="Refresh", width=80, fg_color="#334155", command=self.refresh_table).pack(side="right", padx=12)

        # Table Container
        table_card = ctk.CTkFrame(self, fg_color=COLOR_BG_CARD, corner_radius=12, border_width=1, border_color="#334155")
        table_card.pack(fill="both", expand=True, padx=15, pady=(5, 15))

        # Table Header
        th = ctk.CTkFrame(table_card, fg_color="#0f172a", corner_radius=6, height=35)
        th.pack(fill="x", padx=8, pady=(8, 4))
        ctk.CTkLabel(th, text="STUDENT ID", width=120, font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_MUTED).pack(side="left", padx=5)
        ctk.CTkLabel(th, text="FULL NAME", width=180, font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_MUTED, anchor="w").pack(side="left", padx=5)
        ctk.CTkLabel(th, text="PHONE", width=120, font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_MUTED).pack(side="left", padx=5)
        ctk.CTkLabel(th, text="SEAT", width=80, font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_MUTED).pack(side="left", padx=5)
        ctk.CTkLabel(th, text="STATUS", width=80, font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_MUTED).pack(side="left", padx=5)
        ctk.CTkLabel(th, text="ACTIONS", width=160, font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_MUTED).pack(side="right", padx=15)

        self.table_body = ctk.CTkScrollableFrame(table_card, fg_color="transparent")
        self.table_body.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self.refresh_table()

    def refresh_table(self):
        for w in self.table_body.winfo_children():
            w.destroy()

        q = self.search_entry.get().strip()
        status = self.status_filter.get()
        students = list_students(query=q if q else None, status_filter=status)

        if not students:
            ctk.CTkLabel(self.table_body, text="No students match the criteria.", text_color=COLOR_MUTED).pack(pady=30)
            return

        for std in students:
            row = ctk.CTkFrame(self.table_body, fg_color="#0f172a", corner_radius=8, height=45)
            row.pack(fill="x", pady=2, padx=2)

            ctk.CTkLabel(row, text=std["student_id"], width=120, font=ctk.CTkFont(family="Courier", size=12, weight="bold"), text_color="#818cf8").pack(side="left", padx=5)
            ctk.CTkLabel(row, text=std["full_name"], width=180, font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(row, text=std["phone"] or "N/A", width=120, font=ctk.CTkFont(family="Courier", size=11), text_color=COLOR_MUTED).pack(side="left", padx=5)
            
            seat_badge = ctk.CTkLabel(row, text=f" {std['assigned_seat'] or 'None'} ", font=ctk.CTkFont(family="Courier", size=11, weight="bold"), fg_color="#312e81", text_color="#c7d2fe", corner_radius=4)
            seat_badge.pack(side="left", padx=15)

            st_color = COLOR_SUCCESS if std["status"] == "ACTIVE" else "#64748b"
            st_badge = ctk.CTkLabel(row, text=f" {std['status']} ", font=ctk.CTkFont(size=10, weight="bold"), text_color="#ffffff", fg_color=st_color, corner_radius=4)
            st_badge.pack(side="left", padx=10)

            btn_box = ctk.CTkFrame(row, fg_color="transparent")
            btn_box.pack(side="right", padx=10)

            ctk.CTkButton(btn_box, text="📇 QR Pass", width=80, height=26, font=ctk.CTkFont(size=11), fg_color=COLOR_PRIMARY, command=lambda s=std: self.show_qr_card(s)).pack(side="left", padx=2)
            
            toggle_text = "Deactivate" if std["status"] == "ACTIVE" else "Activate"
            ctk.CTkButton(btn_box, text=toggle_text, width=80, height=26, font=ctk.CTkFont(size=11), fg_color="#334155", hover_color="#475569", command=lambda s=std: self.toggle_status(s["student_id"])).pack(side="left", padx=2)

    def toggle_status(self, student_id: str):
        toggle_student_status(student_id)
        self.refresh_table()
        self.app.screens["dashboard"].refresh_data()
        self.app.screens["seats"].refresh_grid()

    def show_qr_card(self, std: dict):
        """Open high-res student passcard preview dialog."""
        modal = ctk.CTkToplevel(self)
        modal.title(f"QR Attendance Pass - {std['full_name']}")
        modal.geometry("440x620")
        modal.resizable(False, False)
        modal.grab_set()

        card_path = generate_student_id_card(std["student_id"], std["full_name"], std["assigned_seat"] or "UNASSIGNED")
        
        pil_img = Image.open(card_path)
        pil_img_resized = pil_img.resize((350, 476))
        ctk_card = ctk.CTkImage(light_image=pil_img_resized, dark_image=pil_img_resized, size=(350, 476))

        ctk.CTkLabel(modal, text="Official Attendance QR Pass", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(12, 4))
        
        card_lbl = ctk.CTkLabel(modal, image=ctk_card, text="")
        card_lbl.pack(pady=5)

        action_box = ctk.CTkFrame(modal, fg_color="transparent")
        action_box.pack(fill="x", padx=30, pady=10)

        def on_print():
            msg_win = ctk.CTkToplevel(modal)
            msg_win.geometry("300x120")
            msg_win.title("Print Sent")
            ctk.CTkLabel(msg_win, text=f"Card sent to default printer:\n{card_path.name}", font=ctk.CTkFont(size=12)).pack(pady=20)
            ctk.CTkButton(msg_win, text="OK", width=80, command=msg_win.destroy).pack()

        ctk.CTkButton(action_box, text="🖨️ Print Pass Card", fg_color=COLOR_PRIMARY, font=ctk.CTkFont(weight="bold"), command=on_print).pack(side="left", fill="x", expand=True, padx=4)
        ctk.CTkButton(action_box, text="Close", fg_color="#334155", command=modal.destroy).pack(side="left", fill="x", expand=True, padx=4)

    def open_add_modal(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Register New Student")
        modal.geometry("450x480")
        modal.resizable(False, False)
        modal.grab_set()

        ctk.CTkLabel(modal, text="New Student Registration", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10))

        form = ctk.CTkFrame(modal, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=25, pady=5)

        ctk.CTkLabel(form, text="Full Name *", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(5, 2))
        name_entry = ctk.CTkEntry(form, placeholder_text="e.g. Vikas Kumar")
        name_entry.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(form, text="Phone Contact (Optional)", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(5, 2))
        phone_entry = ctk.CTkEntry(form, placeholder_text="e.g. +91 98765 00000")
        phone_entry.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(form, text="Assign Desk / Seat", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(5, 2))
        available_seats = get_available_seats()
        seat_options = ["(Leave Unassigned)"] + [f"{s['seat_number']} - {s['zone']}" for s in available_seats]
        seat_menu = ctk.CTkOptionMenu(form, values=seat_options)
        seat_menu.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(form, text="Notes / Exam Batch", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(5, 2))
        notes_entry = ctk.CTkEntry(form, placeholder_text="e.g. UPSC / Morning Shift")
        notes_entry.pack(fill="x", pady=(0, 8))

        err_lbl = ctk.CTkLabel(form, text="", text_color=COLOR_DANGER)
        err_lbl.pack(pady=2)

        def on_submit():
            name = name_entry.get().strip()
            if not name:
                err_lbl.configure(text="Please enter student full name.")
                return
            
            selected_seat_str = seat_menu.get()
            chosen_seat = ""
            if selected_seat_str and not selected_seat_str.startswith("("):
                chosen_seat = selected_seat_str.split(" - ")[0]

            try:
                res = create_student(
                    full_name=name,
                    phone=phone_entry.get().strip(),
                    assigned_seat=chosen_seat,
                    notes=notes_entry.get().strip()
                )
                modal.destroy()
                self.refresh_table()
                self.app.screens["dashboard"].refresh_data()
                self.app.screens["seats"].refresh_grid()
                self.show_qr_card(res)
            except Exception as ex:
                err_lbl.configure(text=str(ex))

        btn_box = ctk.CTkFrame(modal, fg_color="transparent")
        btn_box.pack(fill="x", padx=25, pady=(0, 20))

        ctk.CTkButton(btn_box, text="Save & Generate QR Card", fg_color=COLOR_PRIMARY, font=ctk.CTkFont(weight="bold"), command=on_submit).pack(side="left", fill="x", expand=True, padx=4)
        ctk.CTkButton(btn_box, text="Cancel", fg_color="#334155", command=modal.destroy).pack(side="left", fill="x", expand=True, padx=4)
