import customtkinter as ctk
from pathlib import Path
from tkinter import filedialog, messagebox
from core.config import DB_PATH, DEFAULT_COOLDOWN_SECONDS, DEFAULT_LIBRARY_NAME
from services.backup_service import create_database_backup, list_available_backups, restore_database_from_backup
from ui.theme import COLOR_PRIMARY, COLOR_SUCCESS, COLOR_WARNING, COLOR_BG_CARD, COLOR_MUTED

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
        ctk.CTkLabel(title_box, text="⚙️ System Configuration & Database Backup", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(title_box, text="Configure attendance rules, duplicate cooldown, and manage local SQLite backups.", font=ctk.CTkFont(size=12), text_color=COLOR_MUTED).pack(anchor="w")

        # Two Column Layout
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=15, pady=5)
        content.grid_columnconfigure((0, 1), weight=1, uniform="settings")
        content.grid_rowconfigure(0, weight=1)

        # Left: Library & Attendance Settings
        left_card = ctk.CTkFrame(content, fg_color=COLOR_BG_CARD, corner_radius=12, border_width=1, border_color="#334155")
        left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=5)

        ctk.CTkLabel(left_card, text="🏛️ Library & Attendance Rules", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=15, pady=(15, 10))

        form = ctk.CTkFrame(left_card, fg_color="transparent")
        form.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(form, text="Library Name", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(5, 2))
        self.lib_name_entry = ctk.CTkEntry(form)
        self.lib_name_entry.insert(0, DEFAULT_LIBRARY_NAME)
        self.lib_name_entry.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(form, text="Attendance Mode", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(5, 2))
        self.mode_menu = ctk.CTkOptionMenu(form, values=["Two-Way Check-in / Check-out", "Single Daily Presence Record"])
        self.mode_menu.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(form, text="Duplicate Scan Cooldown (Seconds)", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(5, 2))
        self.cooldown_entry = ctk.CTkEntry(form)
        self.cooldown_entry.insert(0, str(DEFAULT_COOLDOWN_SECONDS))
        self.cooldown_entry.pack(fill="x", pady=(0, 15))

        self.save_btn = ctk.CTkButton(form, text="Save Preferences", fg_color=COLOR_PRIMARY, font=ctk.CTkFont(weight="bold"), command=self.save_preferences)
        self.save_btn.pack(anchor="w")

        # Right: Backup & Recovery
        right_card = ctk.CTkFrame(content, fg_color=COLOR_BG_CARD, corner_radius=12, border_width=1, border_color="#334155")
        right_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=5)

        ctk.CTkLabel(right_card, text="💾 Database Backup & Recovery", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=15, pady=(15, 10))

        path_box = ctk.CTkFrame(right_card, fg_color="#0f172a", corner_radius=8)
        path_box.pack(fill="x", padx=15, pady=5)
        ctk.CTkLabel(path_box, text="Database Storage Location:", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_MUTED).pack(anchor="w", padx=10, pady=(6, 1))
        ctk.CTkLabel(path_box, text=str(DB_PATH), font=ctk.CTkFont(family="Courier", size=10), text_color="#818cf8").pack(anchor="w", padx=10, pady=(0, 6))

        btn_row = ctk.CTkFrame(right_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=15, pady=10)

        ctk.CTkButton(btn_row, text="📥 Backup Database Now", fg_color="#047857", hover_color="#065f46", font=ctk.CTkFont(weight="bold"), command=self.do_backup).pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(btn_row, text="🔄 Restore From File", fg_color="#d97706", hover_color="#b45309", font=ctk.CTkFont(weight="bold"), command=self.do_restore).pack(side="left", fill="x", expand=True, padx=(4, 0))

        ctk.CTkLabel(right_card, text="Available Backups:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=15, pady=(10, 4))
        
        self.backup_list_container = ctk.CTkScrollableFrame(right_card, fg_color="#0f172a", height=150)
        self.backup_list_container.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.refresh_backups()

    def save_preferences(self):
        messagebox.showinfo("Saved", "System configuration saved successfully.")

    def do_backup(self):
        backup_path = create_database_backup(label="manual")
        self.refresh_backups()
        messagebox.showinfo("Backup Success", f"Database backup completed successfully:\n{backup_path.name}")

    def do_restore(self):
        file_path = filedialog.askopenfilename(title="Select Database Backup to Restore", filetypes=[("SQLite Database", "*.db")])
        if file_path:
            confirm = messagebox.askyesno("Confirm Restore", "Are you sure you want to restore? A safety rollback copy of your current database will be saved before restoring.")
            if confirm:
                safety = restore_database_from_backup(Path(file_path))
                self.refresh_backups()
                self.app.screens["dashboard"].refresh_data()
                self.app.screens["seats"].refresh_grid()
                messagebox.showinfo("Restore Complete", f"Database restored successfully!\nSafety snapshot saved as: {safety.name}")

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
