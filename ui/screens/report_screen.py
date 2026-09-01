import customtkinter as ctk
from pathlib import Path
from tkinter import filedialog, messagebox
from services.report_service import get_student_summary_dataframe, export_attendance_to_excel, export_attendance_to_csv
from ui.theme import COLOR_PRIMARY, COLOR_SUCCESS, COLOR_DANGER, COLOR_BG_CARD, COLOR_MUTED

class ReportScreen(ctk.CTkFrame):
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
        ctk.CTkLabel(title_box, text="📈 Attendance Reports & Data Export", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(title_box, text="Export comprehensive student-wise attendance logs directly to Microsoft Excel (.xlsx) or CSV.", font=ctk.CTkFont(size=12), text_color=COLOR_MUTED).pack(anchor="w")

        btn_box = ctk.CTkFrame(top, fg_color="transparent")
        btn_box.pack(side="right", padx=15, pady=10)

        ctk.CTkButton(btn_box, text="📊 Export Excel (.xlsx)", fg_color="#047857", hover_color="#065f46", font=ctk.CTkFont(weight="bold"), command=self.export_excel).pack(side="left", padx=5)
        ctk.CTkButton(btn_box, text="📄 Export CSV", fg_color="#334155", hover_color="#475569", command=self.export_csv).pack(side="left", padx=5)

        # Content Card
        content_card = ctk.CTkFrame(self, fg_color=COLOR_BG_CARD, corner_radius=12, border_width=1, border_color="#334155")
        content_card.pack(fill="both", expand=True, padx=15, pady=(5, 15))

        self.status_banner = ctk.CTkLabel(content_card, text="", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLOR_SUCCESS)
        self.status_banner.pack(pady=(8, 0))

        th = ctk.CTkFrame(content_card, fg_color="#0f172a", corner_radius=6, height=35)
        th.pack(fill="x", padx=12, pady=(8, 4))
        ctk.CTkLabel(th, text="STUDENT NAME", width=180, font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_MUTED, anchor="w").pack(side="left", padx=5)
        ctk.CTkLabel(th, text="TOKEN", width=110, font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_MUTED).pack(side="left", padx=5)
        ctk.CTkLabel(th, text="SEAT", width=80, font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_MUTED).pack(side="left", padx=5)
        ctk.CTkLabel(th, text="DAYS PRESENT", width=110, font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_MUTED).pack(side="left", padx=5)
        ctk.CTkLabel(th, text="CHECK-INS", width=90, font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_MUTED).pack(side="left", padx=5)
        ctk.CTkLabel(th, text="CHECK-OUTS", width=90, font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_MUTED).pack(side="left", padx=5)
        ctk.CTkLabel(th, text="LAST SEEN", width=160, font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_MUTED).pack(side="right", padx=15)

        self.summary_body = ctk.CTkScrollableFrame(content_card, fg_color="transparent")
        self.summary_body.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.refresh_summary()

    def refresh_summary(self):
        for w in self.summary_body.winfo_children():
            w.destroy()

        df = get_student_summary_dataframe()
        if df.empty:
            ctk.CTkLabel(self.summary_body, text="No attendance aggregations recorded yet.", text_color=COLOR_MUTED).pack(pady=30)
            return

        for _, row in df.iterrows():
            r_frame = ctk.CTkFrame(self.summary_body, fg_color="#0f172a", corner_radius=8, height=40)
            r_frame.pack(fill="x", pady=2, padx=2)

            ctk.CTkLabel(r_frame, text=str(row["Student Name"]), width=180, font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(r_frame, text=str(row["Student Token"]), width=110, font=ctk.CTkFont(family="Courier", size=11), text_color="#818cf8").pack(side="left", padx=5)
            ctk.CTkLabel(r_frame, text=f"Seat {row['Assigned Seat']}", width=80, font=ctk.CTkFont(family="Courier", size=11), text_color="#c7d2fe").pack(side="left", padx=5)
            ctk.CTkLabel(r_frame, text=f"{row['Days Present']} Days", width=110, font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_SUCCESS).pack(side="left", padx=5)
            ctk.CTkLabel(r_frame, text=str(row.get("Check-Ins", "--")), width=90, font=ctk.CTkFont(size=11)).pack(side="left", padx=5)
            ctk.CTkLabel(r_frame, text=str(row.get("Check-Outs", "--")), width=90, font=ctk.CTkFont(size=11)).pack(side="left", padx=5)
            ctk.CTkLabel(r_frame, text=str(row["Last Seen"]).split(".")[0], width=160, font=ctk.CTkFont(family="Courier", size=11), text_color=COLOR_MUTED).pack(side="right", padx=15)

    def export_excel(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Workbook", "*.xlsx")])
        if file_path:
            try:
                out = export_attendance_to_excel(Path(file_path))
                self.status_banner.configure(text=f"✓ Excel report exported successfully: {Path(out).name}", text_color=COLOR_SUCCESS)
                messagebox.showinfo("Export Successful", f"Excel report saved successfully:\n{out}")
            except Exception as e:
                self.status_banner.configure(text=f"Export failed: {str(e)}", text_color=COLOR_DANGER)
                messagebox.showerror("Export Failed", str(e))

    def export_csv(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV File", "*.csv")])
        if file_path:
            try:
                out = export_attendance_to_csv(Path(file_path))
                self.status_banner.configure(text=f"✓ CSV report exported successfully: {Path(out).name}", text_color=COLOR_SUCCESS)
                messagebox.showinfo("Export Successful", f"CSV report saved successfully:\n{out}")
            except Exception as e:
                self.status_banner.configure(text=f"Export failed: {str(e)}", text_color=COLOR_DANGER)
                messagebox.showerror("Export Failed", str(e))
