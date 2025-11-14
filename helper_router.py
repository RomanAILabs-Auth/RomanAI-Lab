#!/usr/bin/env python3
# =============================================================
# helper_router.py
# RomanAI Lab — Unified Helper Routing System
#
# Loads and manages all helper backends:
#   - helper_scriptor
#   - helper_master
#   - helper_micro
#   - helper_patcher
#   - helper_multimodel
#   - tool_rewriter
#
# Provides:
#   router.run_scriptor(prompt)
#   router.run_master(prompt)
#   router.run_micro(prompt)
#   router.run_patcher(prompt)
#   router.run_multimodel(prompt)
#   router.run_rewriter(prompt)
#
# Master must supply:
#   master.status
#   master.cfg
#
# No Spacetime Engine is touched here — helpers handle that.
# =============================================================

import traceback


class HelperRouter:
    def __init__(self, master):
        self.master = master

        # Backend placeholders
        self.scriptor = None
        self.masterbrain = None
        self.micro = None
        self.patcher = None
        self.multimodel = None
        self.rewriter = None

        self._load_all_backends()

    # ------------------------------------------------------------
    # LOAD ALL HELPERS
    # ------------------------------------------------------------
    def _load_all_backends(self):
        """Load helper modules safely, ignore if missing."""

        self.master.status.config(text="Loading helper modules...")

        # Scriptor
        try:
            from helper_scriptor import run as SCRIPTOR
            self.scriptor = SCRIPTOR
        except Exception:
            self._warn("helper_scriptor")

        # Master high-level brain
        try:
            from helper_master import run as MASTER
            self.masterbrain = MASTER
        except Exception:
            self._warn("helper_master")

        # Micro helper
        try:
            from helper_micro import run as MICRO
            self.micro = MICRO
        except Exception:
            self._warn("helper_micro")

        # Patcher backend
        try:
            from helper_patcher import run as PATCHER
            self.patcher = PATCHER
        except Exception:
            self._warn("helper_patcher")

        # MultiModel backend
        try:
            from helper_multimodel import run as MULTI
            self.multimodel = MULTI
        except Exception:
            self._warn("helper_multimodel")

        # Rewriter tool
        try:
            from tool_rewriter import run as REWRITE
            self.rewriter = REWRITE
        except Exception:
            self._warn("tool_rewriter")

        self.master.status.config(text="Helper modules loaded ✓")

    # ------------------------------------------------------------
    # INTERNAL WARNING
    # ------------------------------------------------------------
    def _warn(self, name: str):
        """Warn in UI if a helper fails to load."""
        self.master.status.config(text=f"Warning: {name} missing")

    # ------------------------------------------------------------
    # RUNNERS
    # ------------------------------------------------------------
    def run_scriptor(self, prompt: str) -> str:
        if not self.scriptor:
            return "[Scriptor backend missing]"
        try:
            return self.scriptor(prompt)
        except Exception as e:
            return f"[Scriptor error: {e}]"

    def run_master(self, prompt: str) -> str:
        if not self.masterbrain:
            return "[Master backend missing]"
        try:
            return self.masterbrain(prompt)
        except Exception as e:
            return f"[Master backend error: {e}]"

    def run_micro(self, prompt: str) -> str:
        if not self.micro:
            return "[Micro backend missing]"
        try:
            return self.micro(prompt)
        except Exception as e:
            return f"[Micro backend error: {e}]"

    def run_patcher(self, prompt: str) -> str:
        if not self.patcher:
            return "[Patcher backend missing]"
        try:
            return self.patcher(prompt)
        except Exception as e:
            return f"[Patcher backend error: {e}]"

    def run_multimodel(self, prompt: str) -> str:
        if not self.multimodel:
            return "[MultiModel backend missing]"
        try:
            return self.multimodel(prompt)
        except Exception as e:
            return f"[MultiModel error: {e}]"

    def run_rewriter(self, prompt: str) -> str:
        if not self.rewriter:
            return "[Rewriter backend missing]"
        try:
            return self.rewriter(prompt)
        except Exception as e:
            return f"[Rewriter error: {e}]"

    # ------------------------------------------------------------
    # UNIVERSAL RUNNER (Optional)
    # ------------------------------------------------------------
    def run(self, backend: str, prompt: str) -> str:
        """
        A generic wrapper:
            router.run("scriptor", "do this")
        """
        backend = backend.lower()

        table = {
            "scriptor": self.run_scriptor,
            "master": self.run_master,
            "micro": self.run_micro,
            "patcher": self.run_patcher,
            "multimodel": self.run_multimodel,
            "rewriter": self.run_rewriter,
        }

        if backend not in table:
            return f"[Unknown backend: {backend}]"

        return table[backend](prompt)
# Helper router stub
