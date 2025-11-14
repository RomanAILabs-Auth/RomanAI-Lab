#!/usr/bin/env python3
# =============================================================
# code_feeder.py
# RomanAI Lab — Modular Code Feeder & Buffer Manager
#
# Handles:
#   - Loading files into editor
#   - Showing line numbers
#   - Scroll syncing between lines/text
#   - Chunking code for AI digestion
#   - Updating progress bar + labels
#
# =============================================================

import tkinter as tk
from tkinter import filedialog
from typing import List
import lab_utils as lu


class CodeFeeder:
    """Modular code feeder, line number manager, and chunk generator."""

    def __init__(self, master):
        self.master = master

        # Sync on text modification
        self.master.code_text.bind("<<Modified>>", self._on_text_change)

    # ------------------------------------------------------------
    # FILE LOADING
    # ------------------------------------------------------------
    def load_file(self):
        path = filedialog.askopenfilename(
            title="Open code file",
            filetypes=[("All files", "*.*")]
        )

        if not path:
            return

        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                data = f.read()

            # Put data into editor
            self.master.code_text.delete("1.0", tk.END)
            self.master.code_text.insert("1.0", data)

            # Track buffer source
            self.master.code_buffer["source"] = path
            self.master.save_code_buffer(self.master.code_buffer)

            # Update line numbers
            self._update_line_numbers()

            self.master.status.config(text=f"Loaded: {path}")

        except Exception as e:
            self.master.status.config(text=f"Load error: {e}")

    # ------------------------------------------------------------
    # LINE NUMBER LOGIC
    # ------------------------------------------------------------
    def _on_text_change(self, event=None):
        self.master.code_text.edit_modified(False)
        self._update_line_numbers()

    def _update_line_numbers(self):
        """Build left-side line number column."""
        lines_widget = self.master.code_lines
        text_widget = self.master.code_text

        lines_widget.config(state=tk.NORMAL)
        lines_widget.delete("1.0", tk.END)

        last_index = text_widget.index("end-1c")
        total = int(last_index.split(".")[0])

        buf = [f"{i:5d}\n" for i in range(1, total + 1)]
        lines_widget.insert("1.0", "".join(buf))

        lines_widget.config(state=tk.DISABLED)

    # ------------------------------------------------------------
    # SYNC SCROLLING
    # ------------------------------------------------------------
    def sync_scroll(self, *args):
        """Keep text and line numbers aligned."""
        try:
            self.master.code_text.yview(*args)
            self.master.code_lines.yview(*args)
        except Exception:
            pass

    # ------------------------------------------------------------
    # FEED BUFFER (Chunk code for AI)
    # ------------------------------------------------------------
    def feed_buffer(self):
        """Chunk editor text and store in master.code_buffer."""

        text = self.master.code_text.get("1.0", tk.END)
        lines = text.splitlines()

        if not lines:
            self.master.digestion_label.config(text="Digestion: empty")
            return

        n_lines = len(lines)
        self.master.digestion_label.config(text=f"Digesting {n_lines} lines...")
        self.master.update_idletasks()

        # Chunk with shared utility
        chunks = lu.chunk_text(text, 6000)
        n_chunks = len(chunks)

        self.master.code_buffer["chunks"] = chunks
        self.master.code_buffer["lines"] = n_lines
        self.master.save_code_buffer(self.master.code_buffer)

        self.master.digestion_bar["value"] = 100
        self.master.digestion_label.config(
            text=f"Digested {n_lines} lines → {n_chunks} chunk(s)"
        )
        self.master.status.config(text=f"Buffer ready: {n_chunks} chunks")

