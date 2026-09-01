import customtkinter as ctk
from pathlib import Path
from tkinter import filedialog, messagebox
from core.config import DB_PATH, DEFAULT_COOLDOWN_SECONDS, DEFAULT_LIBRARY_NAME, DEFAULT_ATTENDANCE_MODE
from core.database import get_connection
from services.backup_service import create_database_backup, list_available_backups, restore_database_from_backup
from services.auth_service import change_admin_password
from ui.theme import COLOR_PRIMARY, COLOR_SUCCESS, COLOR_WARNING, COLOR_DANGER, COLOR_BG_CARD, COLOR_MUTED

class SettingsScreen(ctk.CTkFrame):
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
        ctk.CTkLabel(title_box, text="⚙️ System Configuration & Database Safety", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(title_box, text="Configure attendance rules, duplicate cooldown interval, and local SQLite backups.", font=ctk.CTkFont(size=12), text_color=COLOR_MUTED).pack(anchor="w")

        # Two Column Layout
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=15, pady=5)
        content.grid_columnconfigure((0, 1), weight=1, uniform="settings")
        content.grid_rowconfigure(0, weight=1)

        # Left: Library & Attendance Settings
        left_card = ctk.CTkFrame(content, fg_color=COLOR_BG_CARD, corner_radius=12, border_width=1, border_color="#334155")
        left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=5)

        ctk.CTkLabel(left_card, text="🏛️ Library Preferences & Policy", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=15, pady=(15, 10))

        form = ctk.CTkFrame(left_card, fg_color="transparent")
        form.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(form, text="Library Name", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(5, 2))
        self.lib_name_entry = ctk.CTkEntry(form)
        self.lib_name_entry.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(form, text="Attendance Mode", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(5, 2))
        self.mode_menu = ctk.CTkOptionMenu(form, values=["CHECKIN_CHECKOUT", "DAILY_PRESENCE"])
        self.mode_menu.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(form, text="Duplicate Scan Cooldown (Seconds)", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(5, 2))
        self.cooldown_entry = ctk.CTkEntry(form)
        self.cooldown_entry.pack(fill="x", pady=(0, 15))

        btn_row = ctk.CTkFrame(form, fg_color="transparent")
        btn_row.pack(fill="x", pady=5)

        self.save_btn = ctk.CTkButton(btn_row, text="Save Preferences", fg_color=COLOR_PRIMARY, font=ctk.CTkFont(weight="bold"), command=self.save_preferences)
        self.save_btn.pack(side="left", padx=(0, 8))

        self.pw_btn = ctk.CTkButton(btn_row, text="Change Password", fg_color="#334155", hover_color="#475569", command=self.open_change_pw_modal)
        self.pw_btn.pack(side="left")

        # Right: Backup & Recovery
        right_card = ctk.CTkFrame(content, fg_color=COLOR_BG_CARD, corner_radius=12, border_width=1, border_color="#334155")
        right_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=5)

        ctk.CTkLabel(right_card, text="💾 Database Backup & Recovery", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=15, pady=(15, 10))

        path_box = ctk.CTkFrame(right_card, fg_color="#0f172a", corner_radius=8)
        path_box.pack(fill="x", padx=15, pady=5)
        ctk.CTkLabel(path_box, text="Database Storage Location:", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_MUTED).pack(anchor="w", padx=10, pady=(6, 1))
        ctk.CTkLabel(path_box, text=str(DB_PATH), font=ctk.CTkFont(family="Courier", size=10), text_color="#818cf8").pack(anchor="w", padx=10, pady=(0, 6))

        backup_btns = ctk.CTkFrame(right_card, fg_color="transparent")
        backup_btns.pack(fill="x", padx=15, pady=10)

        ctk.CTkButton(backup_btns, text="📥 Backup Database Now", fg_color="#047857", hover_color="#065f46", font=ctk.CTkFont(weight="bold"), command=self.do_backup).pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(backup_btns, text="🔄 Restore From File", fg_color="#d97706", hover_color="#b45309", font=ctk.CTkFont(weight="bold"), command=self.do_restore).pack(side="left", fill="x", expand=True, padx=(4, 0))

        ctk.CTkLabel(right_card, text="Available Backups:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=15, pady=(10, 4))
        
        self.backup_list_container = ctk.CTkScrollableFrame(right_card, fg_color="#0f172a", height=150)
        self.backup_list_container.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.load_settings()
        self.refresh_backups()

    def load_settings(self):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM settings")
            s = {r["key"]: r["value"] for r in cursor.fetchall()}
            self.lib_name_entry.delete(0, "end")
            self.lib_name_entry.insert(0, s.get("library_name", DEFAULT_LIBRARY_NAME))
            
            self.mode_menu.set(s.get("attendance_mode", DEFAULT_ATTENDANCE_MODE))
            
            self.cooldown_entry.delete(0, "end")
            self.cooldown_entry.insert(0, s.get("cooldown_seconds", str(DEFAULT_COOLDOWN_SECONDS)))
        finally:
            conn.close()

    def save_preferences(self):
        lib_name = self.lib_name_entry.get().strip() or DEFAULT_LIBRARY_NAME
        mode = self.mode_menu.get()
        cooldown_str = self.cooldown_entry.get().strip()

        try:
            cooldown_val = int(cooldown_str)
            if cooldown_val < 5:
                raise ValueError("Cooldown must be at least 5 seconds.")
        except ValueError as e:
            messagebox.showerror("Invalid Cooldown", str(e))
            return

        conn = get_connection()
        try:
            cursor = conn.cursor()
            with conn:
                cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", ("library_name", lib_name))
                cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", ("attendance_mode", mode))
                cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", ("cooldown_seconds", str(cooldown_val)))
                cursor.execute("""
                    INSERT INTO audit_logs (action, entity_type, entity_id, details)
                    VALUES (?, ?, ?, ?)
                """, ("SETTINGS_SAVED", "settings", "global", f"Updated library_name: {lib_name}, mode: {mode}, cooldown: {cooldown_val}s"))
            messagebox.showinfo("Saved", "System preferences saved successfully.")
        finally:
            conn.close()

    def open_change_pw_modal(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Change Admin Password")
        modal.geometry("380x320")
        modal.resizable(False, False)
        modal.grab_set()

        ctk.CTkLabel(modal, text="Update Admin Password", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(15, 10))

        f = ctk.CTkFrame(modal, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=25, pady=5)

        ctk.CTkLabel(f, text="Current Password").pack(anchor="w", pady=(2, 1))
        cur_entry = ctk.CTkEntry(f, show="•")
        cur_entry.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(f, text="New Password (min 4 chars)").pack(anchor="w", pady=(2, 1))
        new_entry = ctk.CTkEntry(f, show="•")
        new_entry.pack(fill="x", pady=(0, 8))

        err_lbl = ctk.CTkLabel(f, text="", text_color=COLOR_DANGER)
        err_lbl.pack()

        def on_pw_submit():
            cur_p = cur_entry.get()
            new_p = new_entry.get()
            username = self.app.current_user["username"] if self.app.current_user else "admin"

            try:
                change_admin_password(username, cur_p, new_p)
                modal.destroy()
                messagebox.showinfo("Success", "Password updated successfully!")
            except Exception as e:
                err_lbl.configure(text=str(e))

        btn_box = ctk.CTkFrame(modal, fg_color="transparent")
        btn_box.pack(fill="x", padx=25, pady=(0, 20))
        ctk.CTkButton(btn_box, text="Update Password", fg_color=COLOR_PRIMARY, command=on_pw_submit).pack(side="left", fill="x", expand=True, padx=4)
        ctk.CTkButton(btn_box, text="Cancel", fg_color="#334155", command=modal.destroy).pack(side="left", fill="x", expand=True, padx=4)

    def do_backup(self):
        try:
            backup_path = create_database_backup(label="manual")
            self.refresh_backups()
            messagebox.showinfo("Backup Success", f"Database backup created successfully:\n{backup_path.name}")
        except Exception as e:
            messagebox.showerror("Backup Failed", str(e))

    def do_restore(self):
        file_path = filedialog.askopenfilename(title="Select Database Backup to Restore", filetypes=[("SQLite Database", "*.db")])
        if file_path:
            confirm = messagebox.askyesno("Confirm Database Restore", "Are you sure you want to restore? A safety rollback copy of your current database will be saved before restoring.")
            if confirm:
                try:
                    safety = restore_database_from_backup(Path(file_path))
                    self.refresh_backups()
                    self.app.screens["dashboard"].refresh_data()
                    self.app.screens["seats"].refresh_grid()
                    messagebox.showinfo("Restore Complete", f"Database restored successfully!\nSafety snapshot saved as: {safety.name}")
                except Exception as e:
                    messagebox.showerror("Restore Failed", str(e))

    def refresh_backups(self):
        for w in self.backup_list_container.winfo_children():
            w.destroy()

        backups = list_available_backups()
        if not backups:
            ctk.CTkLabel(self.backup_list_container, text="No backups recorded yet.", text_color=COLOR_MUTED).pack(pady=15)
            return

        for b in backups:
            r = ctk.CTkFrame(self.backup_list_container, fg_color="#1e293b", corner_radius=6, height=32)
            r.pack(fill="x", pady=2, padx=2)
            ctk.CTkLabel(r, text=b["filename"], font=ctk.CTkFont(family="Courier", size=10, weight="bold")).pack(side="left", padx=8)
            ctk.CTkLabel(r, text=f"{b['size_kb']} KB", font=ctk.CTkFont(size=10), text_color=COLOR_MUTED).pack(side="right", padx=8)
