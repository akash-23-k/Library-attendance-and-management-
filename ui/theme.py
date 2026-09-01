import customtkinter as ctk

# Color Palette
COLOR_PRIMARY = "#4f46e5"       # Indigo 600
COLOR_PRIMARY_HOVER = "#4338ca" # Indigo 700
COLOR_BG_DARK = "#0f172a"       # Slate 900
COLOR_BG_CARD = "#1e293b"       # Slate 800
COLOR_BG_LIGHT = "#f8fafc"      # Slate 50
COLOR_CARD_LIGHT = "#ffffff"
COLOR_BORDER = "#334155"
COLOR_BORDER_LIGHT = "#e2e8f0"

COLOR_SUCCESS = "#10b981"       # Emerald 500
COLOR_SUCCESS_BG = "#064e3b"
COLOR_WARNING = "#f59e0b"       # Amber 500
COLOR_WARNING_BG = "#78350f"
COLOR_DANGER = "#ef4444"        # Red 500
COLOR_DANGER_BG = "#7f1d1d"
COLOR_MUTED = "#94a3b8"

def apply_app_theme():
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
