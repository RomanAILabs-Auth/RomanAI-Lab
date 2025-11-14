# Utils stub#!/usr/bin/env python3
# =============================================================
# lab_utils.py
# RomanAI Lab — Shared Utility Functions
#
# Provides:
#   - safe file IO
#   - JSON config load/save
#   - timestamp helpers
#   - chunk splitting
#   - text cleaning
#   - memory-safe logging
#   - UI-safe status updates
#
# Used by:
#   - RomanAI_Lab_Master.py
#   - code_feeder.py
#   - autopatcher_core.py
#   - helper_router.py
#   - flask_service.py
# =============================================================

import os
import json
import datetime
from typing import List


# ------------------------------------------------------------
# JSON CONFIG
# ------------------------------------------------------------
def load_json(path: str, default=None):
    """Load JSON safely. If missing/broken, return default."""
    if default is None:
        default = {}

    try:
        if not os.path.exists(path):
            return default
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path: str, data):
    """Safe JSON write."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception:
        return False


# ------------------------------------------------------------
# TIME
# ------------------------------------------------------------
def timestamp():
    """Return canonical timestamp string."""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def stamp_for_filename():
    """Safe timestamp for filenames."""
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


# ------------------------------------------------------------
# SHARED TEXT UTILITIES
# ------------------------------------------------------------
def clean_markdown(text: str) -> str:
    """Remove ``` wrappers from model output."""
    return (
        text.replace("```python", "")
            .replace("```bash", "")
            .replace("```json", "")
            .replace("```", "")
            .strip()
    )


def strip_control_chars(text: str) -> str:
    """Remove control chars that Tkinter may reject."""
    return "".join(c for c in text if ord(c) >= 32 or c in ("\n", "\t"))


# ------------------------------------------------------------
# CHUNKING
# ------------------------------------------------------------
def chunk_text(text: str, max_chars: int = 6000) -> List[str]:
    """Split text on line boundaries."""
    chunks = []
    start = 0
    n = len(text)

    while start < n:
        end = min(start + max_chars, n)
        nl = text.rfind("\n", start, end)
        if nl <= start:
            nl = end
        chunks.append(text[start:nl])
        start = nl

    return [c for c in chunks if c.strip()]


# ------------------------------------------------------------
# SIMPLE LOGGER
# ------------------------------------------------------------
def append_log(path: str, message: str):
    """Append a timestamped log entry."""
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp()}] {message}\n")
    except Exception:
        pass


# ------------------------------------------------------------
# UI SAFE UPDATES (optional)
# ------------------------------------------------------------
def safe_status(app, text: str):
    """Update status bar safely."""
    try:
        app.status.config(text=text)
    except Exception:
        pass


def safe_set_text(widget, text: str):
    """Safely replace all text in a Tk text widget."""
    try:
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
    except Exception:
        pass

