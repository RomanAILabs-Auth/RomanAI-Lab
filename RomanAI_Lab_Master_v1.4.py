#!/usr/bin/env python3
# =============================================================
# RomanAI Lab Master — NovaPro UI v1.6
# Dual Brain Unified Node (Scriptor + Master)
#
# © 2025 Daniel Harding — RomanAILabs
# Co-Architect: Nova (GPT-5.1 Thinking)
# =============================================================

import os
import sys
import threading
from typing import Optional

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Optional extras
try:
    from llama_cpp import Llama  # type: ignore
except Exception:
    Llama = None

try:
    import pyttsx3  # type: ignore

    TTS_ENGINE = pyttsx3.init()
    TTS_ENGINE.setProperty("rate", 150)
except Exception:
    TTS_ENGINE = None

try:
    import speech_recognition as sr  # type: ignore
except Exception:
    sr = None

# Local modules (expected in same folder)
from ui_theme import ThemeManager
from system_monitor import SystemMonitor
from code_feeder import CodeFeeder
from autopatcher_core import AutoPatcher
from helper_router import HelperRouter
from flask_service import FlaskService
import lab_utils as lu

# =============================================================
# Paths / config
# =============================================================
HOME = os.path.expanduser("~")
STATE_DIR = os.path.join(HOME, ".romanai_lab_state")
os.makedirs(STATE_DIR, exist_ok=True)

CONFIG_FILE = os.path.join(STATE_DIR, "config.json")
CODE_BUFFER_FILE = os.path.join(STATE_DIR, "code_buffer.json")
MEMORY_LOG = os.path.join(STATE_DIR, "memory.log")

DEFAULT_CONFIG = {
    "ui": {"theme": "dark"},
    "gguf": {"scriptor_model": "", "master_model": ""},
    "backend": {"scriptor": "Scriptor (GGUF)", "master": "Master (GGUF)"},
}

SCRIPTOR_BACKENDS = [
    "Scriptor (GGUF)",
    "Micro Helper",
    "Patcher Helper",
    "MultiModel Helper",
    "Tool Rewriter",
]

MASTER_BACKENDS = [
    "Master (GGUF)",
    "Master Helper",
    "MultiModel Helper",
]


# =============================================================
# Main application
# =============================================================
class RomanAILabMaster(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("RomanAI Lab Master — NovaPro UI v1.6")
        self.geometry("1500x950")
        self.configure(bg="#000000")

        # Config / state
        self.cfg = lu.load_json(CONFIG_FILE, DEFAULT_CONFIG)
        self.code_buffer = lu.load_json(
            CODE_BUFFER_FILE, {"source": "", "chunks": [], "lines": 0}
        )

        # Theme tracking lists
        self.themable_frames = []
        self.themable_texts = []

        # LLM handles
        self.scriptor_llm: Optional["Llama"] = None
        self.master_llm: Optional["Llama"] = None

        # Thinking flags
        self.thinking_scriptor = False
        self.thinking_master = False
        self.voice_enabled = False

        # Placeholders for helper modules
        self.helper_router: Optional[HelperRouter] = None
        self.system_monitor: Optional[SystemMonitor] = None
        self.code_feeder: Optional[CodeFeeder] = None
        self.autopatcher: Optional[AutoPatcher] = None
        self.flask_service: Optional[FlaskService] = None

        # Build UI first
        self._build_menu()
        self._build_layout()

        # Attach helpers (widgets now exist)
        self.helper_router = HelperRouter(self)
        self.system_monitor = SystemMonitor(self)
        self.code_feeder = CodeFeeder(self)
        self.autopatcher = AutoPatcher(self)
        self.flask_service = FlaskService(self, port=8888)

        # Theme manager
        self.save_config_fn = lambda c: lu.save_json(CONFIG_FILE, c)
        self.theme_manager = ThemeManager(self)

        # Try auto-load models
        self._auto_load_models()

    # ---------------------------------------------------------
    # Menu bar
    # ---------------------------------------------------------
    def _build_menu(self):
        menubar = tk.Menu(self)

        # File
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Quit", command=self.destroy)
        menubar.add_cascade(label="File", menu=file_menu)

        # View
        view_menu = tk.Menu(menubar, tearoff=0)
        theme_menu = tk.Menu(view_menu, tearoff=0)
        theme_menu.add_command(
            label="Dark (Nova)", command=lambda: self.theme_manager.set_dark()
        )
        theme_menu.add_command(
            label="Grey", command=lambda: self.theme_manager.set_grey()
        )
        theme_menu.add_command(
            label="Light", command=lambda: self.theme_manager.set_light()
        )
        view_menu.add_cascade(label="Theme", menu=theme_menu)
        menubar.add_cascade(label="View", menu=view_menu)

        # Tools
        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="Start API Server", command=self._start_server)
        menubar.add_cascade(label="Tools", menu=tools_menu)

        # Help
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Quick Help", command=self._show_help)
        help_menu.add_command(label="About", command=self._show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.config(menu=menubar)

    def _show_help(self):
        msg = (
            "RomanAI Lab Master — NovaPro\n\n"
            "Left / Scriptor: coding brain\n"
            "Right / Master: reasoning brain\n"
            "Bottom-left: Code Feeder\n"
            "Bottom-right: System Monitor\n"
            "Use the dropdowns to switch backends.\n"
        )
        messagebox.showinfo("Help", msg)

    def _show_about(self):
        msg = (
            "RomanAI Lab Master — NovaPro UI v1.6\n"
            "© 2025 Daniel Harding — RomanAILabs\n"
            "Co-Architect: Nova\n"
        )
        messagebox.showinfo("About", msg)

    def _start_server(self):
        if self.flask_service:
            try:
                self.flask_service.start()
                self.status.config(text="API server started on http://localhost:8888")
            except Exception as e:
                messagebox.showerror("Server Error", str(e))
        else:
            messagebox.showinfo("Server", "FlaskService not initialized yet.")

    # ---------------------------------------------------------
    # Layout
    # ---------------------------------------------------------
    def _build_layout(self):
        # Layout grid: 2x2 + footer
        self.grid_rowconfigure(0, weight=7)
        self.grid_rowconfigure(1, weight=3)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Frames left/right
        left = tk.Frame(self, bg="#000000")
        left.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        left.grid_rowconfigure(0, weight=7)
        left.grid_rowconfigure(1, weight=3)
        left.grid_columnconfigure(0, weight=1)
        self.themable_frames.append(left)

        right = tk.Frame(self, bg="#000000")
        right.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        right.grid_rowconfigure(0, weight=7)
        right.grid_rowconfigure(1, weight=3)
        right.grid_columnconfigure(0, weight=1)
        self.themable_frames.append(right)

        self._build_scriptor(left)
        self._build_master(right)
        self._build_feeder(left)
        self._build_system(right)
        self._build_footer()

    # ----------------- SCRIPTOR PANEL ------------------------
    def _build_scriptor(self, parent):
        frame = tk.Frame(
            parent,
            bg="#000000",
            highlightthickness=2,
            highlightbackground="#00AACC",
        )
        frame.grid(row=0, column=0, sticky="nsew", padx=3, pady=3)
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        self.themable_frames.append(frame)

        header = tk.Frame(frame, bg="#000000")
        header.grid(row=0, column=0, sticky="ew")
        self.themable_frames.append(header)

        tk.Label(
            header,
            text="Scriptor — Coding Brain",
            bg="#000000",
            fg="#EFFFFF",
        ).pack(side=tk.LEFT)

        tk.Label(
            header,
            text="Backend:",
            bg="#000000",
            fg="#EFFFFF",
        ).pack(side=tk.LEFT, padx=(10, 2))

        self.scriptor_backend_var = tk.StringVar(
            value=self.cfg["backend"].get("scriptor", "Scriptor (GGUF)")
        )
        self.scriptor_backend_menu = ttk.Combobox(
            header,
            textvariable=self.scriptor_backend_var,
            values=SCRIPTOR_BACKENDS,
            state="readonly",
            width=20,
        )
        self.scriptor_backend_menu.pack(side=tk.LEFT, padx=4)

        self.scriptor_text = tk.Text(
            frame,
            wrap=tk.WORD,
            font=("Courier", 11),
            bg="#000000",
            fg="#EFFFFF",
            insertbackground="#00F0FF",
        )
        self.scriptor_text.grid(row=1, column=0, sticky="nsew")
        self.scriptor_text.tag_config("user", foreground="#80FF80")
        self.scriptor_text.tag_config("ai", foreground="#FF8080")
        self.themable_texts.append(self.scriptor_text)

        s_scroll = tk.Scrollbar(frame, command=self.scriptor_text.yview)
        s_scroll.grid(row=1, column=1, sticky="ns")
        self.scriptor_text.config(yscrollcommand=s_scroll.set)

        entry_frame = tk.Frame(frame, bg="#000000")
        entry_frame.grid(row=2, column=0, columnspan=2, sticky="ew")
        self.themable_frames.append(entry_frame)

        self.scriptor_entry = tk.Entry(
            entry_frame,
            bg="#000000",
            fg="#EFFFFF",
            insertbackground="#00F0FF",
            highlightbackground="#00F0FF",
            highlightcolor="#00F0FF",
            highlightthickness=1,
        )
        self.scriptor_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.scriptor_entry.bind("<Return>", lambda e: self._send("scriptor"))

        tk.Button(
            entry_frame,
            text="Send",
            command=lambda: self._send("scriptor"),
        ).pack(side=tk.RIGHT, padx=4)

    # ----------------- MASTER PANEL -------------------------
    def _build_master(self, parent):
        frame = tk.Frame(
            parent,
            bg="#000000",
            highlightthickness=2,
            highlightbackground="#00AACC",
        )
        frame.grid(row=0, column=0, sticky="nsew", padx=3, pady=3)
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        self.themable_frames.append(frame)

        header = tk.Frame(frame, bg="#000000")
        header.grid(row=0, column=0, sticky="ew")
        self.themable_frames.append(header)

        tk.Label(
            header,
            text="Master Chat — Reasoning Brain",
            bg="#000000",
            fg="#EFFFFF",
        ).pack(side=tk.LEFT)

        tk.Label(
            header,
            text="Backend:",
            bg="#000000",
            fg="#EFFFFF",
        ).pack(side=tk.LEFT, padx=(10, 2))

        self.master_backend_var = tk.StringVar(
            value=self.cfg["backend"].get("master", "Master (GGUF)")
        )
        self.master_backend_menu = ttk.Combobox(
            header,
            textvariable=self.master_backend_var,
            values=MASTER_BACKENDS,
            state="readonly",
            width=20,
        )
        self.master_backend_menu.pack(side=tk.LEFT, padx=4)

        self.master_text = tk.Text(
            frame,
            wrap=tk.WORD,
            font=("Courier", 11),
            bg="#000000",
            fg="#EFFFFF",
            insertbackground="#00F0FF",
        )
        self.master_text.grid(row=1, column=0, sticky="nsew")
        self.master_text.tag_config("user", foreground="#80FF80")
        self.master_text.tag_config("ai", foreground="#FF8080")
        self.themable_texts.append(self.master_text)

        m_scroll = tk.Scrollbar(frame, command=self.master_text.yview)
        m_scroll.grid(row=1, column=1, sticky="ns")
        self.master_text.config(yscrollcommand=m_scroll.set)

        entry_frame = tk.Frame(frame, bg="#000000")
        entry_frame.grid(row=2, column=0, columnspan=2, sticky="ew")
        self.themable_frames.append(entry_frame)

        self.master_entry = tk.Entry(
            entry_frame,
            bg="#000000",
            fg="#EFFFFF",
            insertbackground="#00F0FF",
            highlightbackground="#00F0FF",
            highlightcolor="#00F0FF",
            highlightthickness=1,
        )
        self.master_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.master_entry.bind("<Return>", lambda e: self._send("master"))

        tk.Button(
            entry_frame,
            text="Send",
            command=lambda: self._send("master"),
        ).pack(side=tk.RIGHT, padx=4)

        if sr is not None:
            tk.Button(
                entry_frame,
                text="🎙",
                command=self._mic_to_master,
            ).pack(side=tk.RIGHT, padx=4)

    # ----------------- FEEDER PANEL -------------------------
    def _build_feeder(self, parent):
        frame = tk.Frame(
            parent,
            bg="#000000",
            highlightthickness=2,
            highlightbackground="#00AACC",
        )
        frame.grid(row=1, column=0, sticky="nsew", padx=3, pady=3)
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(1, weight=1)
        self.themable_frames.append(frame)

        tk.Label(
            frame,
            text="Code Feeder — Large File Buffer",
            bg="#000000",
            fg="#EFFFFF",
        ).grid(row=0, column=0, columnspan=3, sticky="w")

        self.code_lines = tk.Text(
            frame,
            width=6,
            bg="#000000",
            fg="#EFFFFF",
            state=tk.DISABLED,
            font=("Courier", 9),
        )
        self.code_lines.grid(row=1, column=0, sticky="nsew")
        self.themable_texts.append(self.code_lines)

        self.code_text = tk.Text(
            frame,
            wrap=tk.NONE,
            bg="#000000",
            fg="#EFFFFF",
            insertbackground="#00F0FF",
            font=("Courier", 9),
        )
        self.code_text.grid(row=1, column=1, sticky="nsew")
        self.themable_texts.append(self.code_text)

        y_scroll = tk.Scrollbar(frame, command=self._feeder_scroll)
        y_scroll.grid(row=1, column=2, sticky="ns")
        self.code_text.config(yscrollcommand=y_scroll.set)
        self.code_lines.config(yscrollcommand=y_scroll.set)

        self.code_text.bind("<MouseWheel>", self._mouse_scroll_sync)
        self.code_lines.bind("<MouseWheel>", self._mouse_scroll_sync)

        x_scroll = tk.Scrollbar(
            frame,
            orient=tk.HORIZONTAL,
            command=self.code_text.xview,
        )
        x_scroll.grid(row=2, column=0, columnspan=3, sticky="ew")
        self.code_text.config(xscrollcommand=x_scroll.set)

        btns = tk.Frame(frame, bg="#000000")
        btns.grid(row=3, column=0, columnspan=3, sticky="ew")
        self.themable_frames.append(btns)

        tk.Button(
            btns,
            text="Load File",
            command=lambda: self.code_feeder and self.code_feeder.load_file(),
        ).pack(side=tk.LEFT, padx=3)
        tk.Button(
            btns,
            text="Clear",
            command=lambda: self.code_text.delete("1.0", tk.END),
        ).pack(side=tk.LEFT, padx=3)
        tk.Button(
            btns,
            text="Feed Buffer",
            command=lambda: self.code_feeder and self.code_feeder.feed_buffer(),
        ).pack(side=tk.LEFT, padx=3)
        tk.Button(
            btns,
            text="Patch",
            command=lambda: self.autopatcher
            and self.autopatcher.patch_current_buffer(),
        ).pack(side=tk.LEFT, padx=3)
        tk.Button(
            btns,
            text="Save Patched",
            command=lambda: self.autopatcher
            and self.autopatcher.save_patched_file(),
        ).pack(side=tk.LEFT, padx=3)

        self.digestion_label = tk.Label(
            btns, text="Digestion: idle", bg="#000000", fg="#EFFFFF"
        )
        self.digestion_label.pack(side=tk.LEFT, padx=4)

        self.digestion_bar = ttk.Progressbar(
            btns, length=150, mode="determinate", maximum=100
        )
        self.digestion_bar.pack(side=tk.LEFT, padx=4)

    def _feeder_scroll(self, *args):
        self.code_text.yview(*args)
        self.code_lines.yview(*args)
        if self.code_feeder:
            self.code_feeder.sync_scroll(*args)

    def _mouse_scroll_sync(self, event):
        delta = int(-1 * (event.delta / 120))
        self.code_text.yview_scroll(delta, "units")
        self.code_lines.yview_scroll(delta, "units")
        return "break"

    # ----------------- SYSTEM PANEL -------------------------
    def _build_system(self, parent):
        frame = tk.Frame(
            parent,
            bg="#000000",
            highlightthickness=2,
            highlightbackground="#00AACC",
        )
        frame.grid(row=1, column=0, sticky="nsew", padx=3, pady=3)
        self.themable_frames.append(frame)

        self.sys_label = tk.Label(
            frame,
            font=("Courier", 10),
            bg="#000000",
            fg="#EFFFFF",
            justify="left",
        )
        self.sys_label.pack(side=tk.TOP, anchor="w")

        self.sys_canvas = tk.Canvas(
            frame,
            bg="#000000",
            height=120,
            highlightthickness=0,
        )
        self.sys_canvas.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

    # ----------------- FOOTER -------------------------------
    def _build_footer(self):
        frame = tk.Frame(self, bg="#000000")
        frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=4)
        self.themable_frames.append(frame)

        tk.Button(
            frame,
            text="Load Scriptor GGUF",
            command=self._load_scriptor_model_dialog,
        ).pack(side=tk.LEFT, padx=4)

        tk.Button(
            frame,
            text="Load Master GGUF",
            command=self._load_master_model_dialog,
        ).pack(side=tk.LEFT, padx=4)

        if TTS_ENGINE is not None:
            self.voice_btn = tk.Button(
                frame, text="Voice OFF", command=self._toggle_voice
            )
            self.voice_btn.pack(side=tk.LEFT, padx=6)

        self.status = tk.Label(
            frame,
            text="RomanAI Lab Master: Idle",
            bg="#000000",
            fg="#EFFFFF",
            anchor="w",
            font=("Courier", 9),
        )
        self.status.pack(side=tk.LEFT, padx=10)

    # =============================================================
    # Model loading
    # =============================================================
    def _auto_load_models(self):
        if Llama is None:
            return
        s_path = self.cfg["gguf"].get("scriptor_model") or ""
        m_path = self.cfg["gguf"].get("master_model") or ""
        if s_path and os.path.exists(s_path):
            self._load_scriptor_model(s_path, quiet=True)
        if m_path and os.path.exists(m_path):
            self._load_master_model(m_path, quiet=True)

    def _load_scriptor_model_dialog(self):
        path = filedialog.askopenfilename(
            title="Select GGUF model for Scriptor",
            filetypes=[("GGUF model", "*.gguf"), ("All files", "*.*")],
        )
        if path:
            self._load_scriptor_model(path)

    def _load_master_model_dialog(self):
        path = filedialog.askopenfilename(
            title="Select GGUF model for Master",
            filetypes=[("GGUF model", "*.gguf"), ("All files", "*.*")],
        )
        if path:
            self._load_master_model(path)

    def _load_scriptor_model(self, path: str, quiet: bool = False):
        if Llama is None:
            if not quiet:
                messagebox.showerror("Error", "llama_cpp is not installed.")
            return
        try:
            threads = max(1, (os.cpu_count() or 4) // 2)
            if not quiet:
                self.status.config(text="Loading Scriptor model...")
                self.update_idletasks()
            self.scriptor_llm = Llama(
                model_path=path,
                n_ctx=8192,
                n_threads=threads,
                n_gpu_layers=-1,
                verbose=False,
            )
            self.cfg["gguf"]["scriptor_model"] = path
            lu.save_json(CONFIG_FILE, self.cfg)
            if not quiet:
                self.status.config(
                    text=f"Scriptor model loaded: {os.path.basename(path)}"
                )
        except Exception as e:
            if not quiet:
                messagebox.showerror("Scriptor Load Error", str(e))
            self.status.config(text="Scriptor model load failed.")

    def _load_master_model(self, path: str, quiet: bool = False):
        if Llama is None:
            if not quiet:
                messagebox.showerror("Error", "llama_cpp is not installed.")
            return
        try:
            threads = max(1, (os.cpu_count() or 4) // 2)
            if not quiet:
                self.status.config(text="Loading Master model...")
                self.update_idletasks()
            self.master_llm = Llama(
                model_path=path,
                n_ctx=8192,
                n_threads=threads,
                n_gpu_layers=-1,
                verbose=False,
            )
            self.cfg["gguf"]["master_model"] = path
            lu.save_json(CONFIG_FILE, self.cfg)
            if not quiet:
                self.status.config(
                    text=f"Master model loaded: {os.path.basename(path)}"
                )
        except Exception as e:
            if not quiet:
                messagebox.showerror("Master Load Error", str(e))
            self.status.config(text="Master model load failed.")

    # =============================================================
    # Chat send / routing
    # =============================================================
    def _send(self, source: str):
        if source == "scriptor":
            entry = self.scriptor_entry
            out = self.scriptor_text
            backend_name = self.scriptor_backend_var.get()
        else:
            entry = self.master_entry
            out = self.master_text
            backend_name = self.master_backend_var.get()

        text = entry.get().strip()
        if not text:
            return
        entry.delete(0, tk.END)

        out.insert(tk.END, f"You: {text}\n", "user")
        out.see(tk.END)
        lu.append_log(MEMORY_LOG, f"[{source.upper()} USER] {text}")

        self.cfg["backend"][source] = backend_name
        lu.save_json(CONFIG_FILE, self.cfg)

        if source == "scriptor":
            if self.thinking_scriptor:
                self._append_ai(out, "RomanAI: Still thinking...\n")
                return
            self.thinking_scriptor = True
        else:
            if self.thinking_master:
                self._append_ai(out, "RomanAI: Still thinking...\n")
                return
            self.thinking_master = True

        if source == "scriptor":
            if backend_name == "Scriptor (GGUF)":
                threading.Thread(
                    target=self._run_scriptor_gguf, args=(text,), daemon=True
                ).start()
            else:
                threading.Thread(
                    target=self._run_helper_backend,
                    args=("scriptor", backend_name, text),
                    daemon=True,
                ).start()
        else:
            if backend_name == "Master (GGUF)":
                threading.Thread(
                    target=self._run_master_gguf, args=(text,), daemon=True
                ).start()
            else:
                threading.Thread(
                    target=self._run_helper_backend,
                    args=("master", backend_name, text),
                    daemon=True,
                ).start()

    def _run_scriptor_gguf(self, prompt: str):
        if not self.scriptor_llm:
            answer = "[No Scriptor GGUF model loaded.]"
        else:
            answer = self._call_llama(self.scriptor_llm, prompt, mode="coding")
        self.after(0, self._finish_turn, "scriptor", answer)

    def _run_master_gguf(self, prompt: str):
        if not self.master_llm:
            answer = "[No Master GGUF model loaded.]"
        else:
            answer = self._call_llama(self.master_llm, prompt, mode="reasoning")
        self.after(0, self._finish_turn, "master", answer)

    def _run_helper_backend(self, source: str, backend_name: str, prompt: str):
        if not self.helper_router:
            answer = "[Helper router not initialized]"
        else:
            if source == "scriptor":
                if backend_name == "Micro Helper":
                    key = "micro"
                elif backend_name == "Patcher Helper":
                    key = "patcher"
                elif backend_name == "MultiModel Helper":
                    key = "multimodel"
                elif backend_name == "Tool Rewriter":
                    key = "rewriter"
                else:
                    key = "scriptor"
            else:
                if backend_name == "Master Helper":
                    key = "master"
                else:
                    key = "multimodel"

            answer = self.helper_router.run(key, prompt)

        self.after(0, self._finish_turn, source, answer)

    def _call_llama(self, llm: "Llama", prompt: str, mode: str) -> str:
        system_content = (
            "You are RomanAI, offline assistant for RomanAILabs.\n"
            "Be precise, helpful, structured, and stable.\n"
        )
        if mode == "coding":
            system_content += "Mode: CODING. Generate correct, well-commented code.\n"
        else:
            system_content += "Mode: REASONING. Think in clear, layered steps.\n"

        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": prompt},
        ]
        try:
            result = llm.create_chat_completion(
                messages=messages,
                max_tokens=2048,
                temperature=0.6,
                stream=False,
            )
            content = result["choices"][0]["message"].get("content", "")
            return lu.clean_markdown(content)
        except Exception as e:
            return f"[LLM error: {e}]"

    def _finish_turn(self, source: str, answer: str):
        out = self.scriptor_text if source == "scriptor" else self.master_text
        self._append_ai(out, f"RomanAI: {answer}\n")
        lu.append_log(MEMORY_LOG, f"[{source.upper()} AI] {answer}")

        if source == "scriptor":
            self.thinking_scriptor = False
        else:
            self.thinking_master = False

        self.status.config(
            text=f"Last turn ({source}): {len(answer)} chars"
        )

        if self.voice_enabled and TTS_ENGINE is not None:
            try:
                TTS_ENGINE.say(answer[:500])
                TTS_ENGINE.runAndWait()
            except Exception:
                pass

    def _append_ai(self, widget: tk.Text, text: str):
        widget.insert(tk.END, text, "ai")
        widget.see(tk.END)

    # =============================================================
    # Voice / mic
    # =============================================================
    def _toggle_voice(self):
        self.voice_enabled = not self.voice_enabled
        if hasattr(self, "voice_btn"):
            self.voice_btn.config(
                text="Voice ON" if self.voice_enabled else "Voice OFF"
            )

    def _mic_to_master(self):
        if sr is None:
            messagebox.showinfo("Mic", "speech_recognition not installed.")
            return
        r = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                self.status.config(text="Listening...")
                audio = r.listen(source, timeout=5, phrase_time_limit=6)
            text = r.recognize_google(audio)
            self.status.config(text=f"Heard: {text}")
            self.master_entry.delete(0, tk.END)
            self.master_entry.insert(0, text)
            self._send("master")
        except Exception as e:
            self.status.config(text=f"Mic error: {e}")


# =============================================================
# Main
# =============================================================
if __name__ == "__main__":
    if sys.platform.startswith("win"):
        try:
            from ctypes import windll

            windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

    app = RomanAILabMaster()
    app.mainloop()

