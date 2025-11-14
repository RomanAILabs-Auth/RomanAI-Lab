#!/usr/bin/env python3
# =============================================================
# autopatcher_core.py
# RomanAI Lab — Modular Autonomous Code Patcher
#
# Handles:
#   - Preparing patch requests
#   - Calling the patcher helper backend
#   - Safe write operations
#   - Patch validation
#   - Different merge strategies
#
# Master must provide:
#   master.code_text           (current text)
#   master.code_buffer         (chunks & source path)
#   master.status              (label)
#   master.helper_router       (router to helpers)
#   master.cfg                 (config)
#
# This module DOES NOT draw UI.
# =============================================================

import os
import difflib
import datetime
from typing import Optional, Tuple


class AutoPatcher:
    """
    Autonomous code patcher for RomanAI Lab.
    Works alongside helper_patcher.py.
    """

    def __init__(self, master):
        self.master = master

    # ------------------------------------------------------------
    # PUBLIC ENTRY: patch current code
    # ------------------------------------------------------------
    def patch_current_buffer(self):
        """
        Patch the current code using the selected backend.
        """
        try:
            current_code = self.master.code_text.get("1.0", "end-1c")

            if not current_code.strip():
                self.master.status.config(text="No code loaded.")
                return

            patch_prompt = self._build_patch_prompt(current_code)
            self.master.status.config(text="Patching... (this may take a moment)")
            self.master.update_idletasks()

            # Request patch from helper router (patcher backend)
            patched = self.master.helper_router.run_patcher(patch_prompt)

            if not patched:
                self.master.status.config(text="Patch failed or returned empty.")
                return

            # Validate + compare
            merged_text, summary = self._validate_and_merge(
                original=current_code,
                patched=patched
            )

            # Push into code editor
            self.master.code_text.delete("1.0", "end")
            self.master.code_text.insert("1.0", merged_text)

            self.master.status.config(text=f"Patch applied ✓ — {summary}")

        except Exception as e:
            self.master.status.config(text=f"Patch error: {e}")

    # ------------------------------------------------------------
    # BUILD PROMPT FOR PATCHER MODEL
    # ------------------------------------------------------------
    def _build_patch_prompt(self, code: str) -> str:
        """
        Build a clean prompt for the patching backend.
        """
        return (
            "You are RomanAI Autonomous Code Patcher.\n"
            "Analyze the following code, fix bugs, repair indentation, "
            "improve stability, and preserve all logic EXACTLY.\n"
            "Do NOT remove math or engine logic. Only repair and stabilize.\n\n"
            "=== ORIGINAL CODE START ===\n"
            f"{code}\n"
            "=== ORIGINAL CODE END ===\n\n"
            "Return ONLY the patched code. No comments. No markdown. No analysis."
        )

    # ------------------------------------------------------------
    # PATCH VALIDATION + MERGE
    # ------------------------------------------------------------
    def _validate_and_merge(self, original: str, patched: str) -> Tuple[str, str]:
        """
        Validate patch, merge if necessary, and generate summary.
        """

        # Clean model output (remove ``` wrappers if present)
        cleaned = patched.replace("```python", "").replace("```", "").strip()

        if not cleaned.strip():
            return original, "Patch empty — reverted"

        # If user wants strict patching:
        if self.master.cfg.get("patching", {}).get("mode", "replace") == "replace":
            return cleaned, "Full replace"

        # Otherwise merge intelligently
        diff = list(difflib.unified_diff(
            original.splitlines(),
            cleaned.splitlines(),
            lineterm=""
        ))

        if not diff:
            return original, "No changes"

        merged = cleaned  # For now, direct merge (can be expanded)

        return merged, f"Patched {len(diff)} changed lines"

    # ------------------------------------------------------------
    # SAVE TO FILE (PATCHED VERSION)
    # ------------------------------------------------------------
    def save_patched_file(self):
        """
        Save patched code as a new version next to the original file.
        """
        try:
            buf = self.master.code_text.get("1.0", "end-1c")
            original_path = self.master.code_buffer.get("source")

            if not original_path:
                self.master.status.config(text="No original file to patch.")
                return

            # Auto naming
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            root, ext = os.path.splitext(original_path)
            new_path = f"{root}_PATCHED_{timestamp}{ext}"

            with open(new_path, "w", encoding="utf-8") as f:
                f.write(buf)

            self.master.status.config(text=f"Saved patched file → {new_path}")

        except Exception as e:
            self.master.status.config(text=f"Save error: {e}")

