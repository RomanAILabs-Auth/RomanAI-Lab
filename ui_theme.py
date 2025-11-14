#!/usr/bin/env python3
# =============================================================
# ui_theme.py
# RomanAI Lab — Basic theme manager with Neo Dark (white-neon)
#
# Themes:
#   - dark  : Neo dark (default) — white neon + quantum cyan on black
#   - grey  : Soft grey panels with white text
#   - light : Light background (for emergencies / screenshots)
#
# Master expects:
#   - app.themable_frames : list[tk.Frame-like]
#   - app.themable_texts  : list[tk.Text-like]
#   - app.save_config_fn(cfg) optional
# =============================================================

import tkinter as tk
from tkinter import ttk


class ThemeManager:
    def __init__(self, app):
        self.app = app
        self.style = ttk.Style(app)

        # Default to dark if missing
        theme = "dark"
        try:
            theme = app.cfg.get("ui", {}).get("theme", "dark")
        except Exception:
            pass

        self.apply_theme(theme)

    # ---------------------------------------------------------
    # Public API used by master menu
    # ---------------------------------------------------------
    def set_dark(self):
        self.apply_theme("dark")

    def set_grey(self):
        self.apply_theme("grey")

    def set_light(self):
        self.apply_theme("light")

    # ---------------------------------------------------------
    # Core
    # ---------------------------------------------------------
    def apply_theme(self, name: str):
        name = name.lower().strip()
        if name not in ("dark", "grey", "light"):
            name = "dark"

        if name == "dark":
            colors = self._neo_dark_colors()
        elif name == "grey":
            colors = self._grey_colors()
        else:
            colors = self._light_colors()

        self._apply_colors(colors)

        # Save back to config if possible
        try:
            self.app.cfg.setdefault("ui", {})["theme"] = name
            if hasattr(self.app, "save_config_fn"):
                self.app.save_config_fn(self.app.cfg)
        except Exception:
            pass

    # ---------------------------------------------------------
    # Palettes
    # ---------------------------------------------------------
    def _neo_dark_colors(self):
        return {
            "bg": "#000000",         # true black
            "panel": "#050810",      # subtle dark blue-ish
            "text": "#EFFFFF",       # white neon
            "accent": "#00F0FF",     # quantum cyan
            "accent_soft": "#0099CC",
            "user": "#80FF80",       # user text (green)
            "ai": "#FF8080",         # ai text (soft red)
        }

    def _grey_colors(self):
        return {
            "bg": "#202020",
            "panel": "#303030",
            "text": "#F0F0F0",
            "accent": "#4DD0E1",
            "accent_soft": "#26A69A",
            "user": "#A5D6A7",
            "ai": "#EF9A9A",
        }

    def _light_colors(self):
        return {
            "bg": "#F5F5F5",
            "panel": "#FFFFFF",
            "text": "#202020",
            "accent": "#1976D2",
            "accent_soft": "#64B5F6",
            "user": "#2E7D32",
            "ai": "#C62828",
        }

    # ---------------------------------------------------------
    # Apply colors to app widgets
    # ---------------------------------------------------------
    def _apply_colors(self, c):
        bg = c["bg"]
        panel = c["panel"]
        text = c["text"]
        accent = c["accent"]
        accent_soft = c["accent_soft"]

        # Root window
        try:
            self.app.configure(bg=bg)
        except Exception:
            pass

        # Frames
        for frame in getattr(self.app, "themable_frames", []):
            try:
                frame.configure(bg=panel, highlightbackground=accent_soft)
            except Exception:
                try:
                    frame.configure(bg=panel)
                except Exception:
                    pass

        # Text widgets
        for txt in getattr(self.app, "themable_texts", []):
            try:
                txt.configure(
                    bg=bg,
                    fg=text,
                    insertbackground=accent,
                    highlightthickness=1,
                    highlightbackground=accent_soft,
                    relief=tk.FLAT,
                )
            except Exception:
                pass

        # Try to recolor status label if present
        for attr in ("status", "digestion_label"):
            lbl = getattr(self.app, attr, None)
            if lbl is not None:
                try:
                    lbl.configure(bg=panel, fg=text)
                except Exception:
                    pass

        # System monitor label (if exists) — ensure black
        sys_label = getattr(self.app, "sys_label", None)
        if sys_label is not None:
            try:
                sys_label.configure(bg="#000000", fg=text)
            except Exception:
                pass

        # Basic ttk style tweaks (scrollbars etc.)
        try:
            self.style.theme_use("default")
        except Exception:
            pass

        # Scrollbars: dark trough, accent slider
        try:
            self.style.configure(
                "Vertical.TScrollbar",
                troughcolor=bg,
                background=accent,
                bordercolor=bg,
                arrowcolor=text,
            )
            self.style.configure(
                "Horizontal.TScrollbar",
                troughcolor=bg,
                background=accent,
                bordercolor=bg,
                arrowcolor=text,
            )
        except Exception:
            pass

