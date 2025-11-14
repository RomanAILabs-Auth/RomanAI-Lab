#!/usr/bin/env python3
# =============================================================
# flask_service.py
# RomanAI Lab — Optional Local Microserver
#
# Exposes a safe, simple API:
#   GET  /ping                -> "pong"
#   POST /scriptor            -> send prompt to Scriptor backend
#   POST /master              -> send prompt to Master backend
#   POST /micro               -> send prompt to Micro backend
#   POST /rewrite             -> send content to rewriter
#   POST /patcher             -> send content to patcher
#
#   GET  /memory/recall       -> recall memory if master exposes API
#   POST /memory/store        -> store memory (optional)
#
# This server:
#   - runs in a separate thread
#   - never blocks UI
#   - uses the helper router
#   - is 100% optional
#
# =============================================================

import threading
import traceback

try:
    from flask import Flask, request, jsonify
except Exception:
    Flask = None  # If Flask is missing, server is silently disabled


class FlaskService:
    """
    A tiny Flask microserver for RomanAI Lab.
    Running on http://127.0.0.1:<port>
    """

    def __init__(self, master, port=8888):
        self.master = master
        self.port = port

        if Flask is None:
            self.master.status.config(text="Flask not installed — server disabled.")
            return

        self.app = Flask("RomanAI_Lab_Server")

        # Register routes
        self._register_routes()

    # ------------------------------------------------------------
    # ROUTES
    # ------------------------------------------------------------
    def _register_routes(self):

        @self.app.route("/ping")
        def ping():
            return jsonify({"status": "ok", "message": "pong"})

        # -----------------------------
        # BACKEND ROUTES
        # -----------------------------
        @self.app.route("/scriptor", methods=["POST"])
        def r_scriptor():
            return self._handle_backend("scriptor")

        @self.app.route("/master", methods=["POST"])
        def r_master():
            return self._handle_backend("master")

        @self.app.route("/micro", methods=["POST"])
        def r_micro():
            return self._handle_backend("micro")

        @self.app.route("/rewrite", methods=["POST"])
        def r_rewrite():
            return self._handle_backend("rewriter")

        @self.app.route("/patcher", methods=["POST"])
        def r_patcher():
            return self._handle_backend("patcher")

        @self.app.route("/multimodel", methods=["POST"])
        def r_multi():
            return self._handle_backend("multimodel")

        # -----------------------------
        # MEMORY ROUTES (Optional)
        # -----------------------------
        @self.app.route("/memory/recall")
        def recall_memory():
            if not hasattr(self.master, "engine"):
                return jsonify({"error": "engine not available"})
            try:
                recall = self.master.engine.recall_memory()
                return jsonify({"recall": recall})
            except Exception as e:
                return jsonify({"error": str(e)})

        @self.app.route("/memory/store", methods=["POST"])
        def store_memory():
            if not hasattr(self.master, "engine"):
                return jsonify({"error": "engine not available"})
            try:
                data = request.json.get("data", "")
                ok = self.master.engine.store_memory(data)
                return jsonify({"stored": ok})
            except Exception as e:
                return jsonify({"error": str(e)})

    # ------------------------------------------------------------
    # BACKEND HANDLER
    # ------------------------------------------------------------
    def _handle_backend(self, backend):
        """
        Generic function to run a helper through router.
        """
        try:
            data = request.json
            prompt = data.get("prompt", "")

            if not prompt.strip():
                return jsonify({"error": "empty prompt"}), 400

            response = self.master.helper_router.run(backend, prompt)

            return jsonify({"backend": backend, "response": response})

        except Exception as e:
            return jsonify({"error": str(e)})

    # ------------------------------------------------------------
    # START SERVER
    # ------------------------------------------------------------
    def start(self):
        """Start Flask server in a separate thread."""

        if Flask is None:
            self.master.status.config(text="Flask unavailable.")
            return

        def _run():
            try:
                self.app.run(
                    host="127.0.0.1",
                    port=self.port,
                    debug=False,
                    use_reloader=False
                )
            except Exception:
                traceback.print_exc()

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

        self.master.status.config(
            text=f"Flask server running at http://127.0.0.1:{self.port}"
        )
# Flask service stub
