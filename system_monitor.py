#!/usr/bin/env python3
# =============================================================
# system_monitor.py
# RomanAI Lab — Neon CPU / RAM / SWAP monitor (vertical bars)
#
# - Full-height vertical CPU bars (2px width, 2px spacing)
# - Quantum-cyan on true black
# - Label text in white neon
# - Safe if psutil or sensors are missing
# =============================================================

import time

ACCENT = "#00F0FF"   # Quantum cyan
TEXT   = "#EFFFFF"   # White neon
BG     = "#000000"   # True black


class SystemMonitor:
    def __init__(self, master):
        """
        master must expose:
            master.sys_canvas : tk.Canvas
            master.sys_label  : tk.Label
        """
        self.master = master
        self.canvas = master.sys_canvas
        self.label = master.sys_label

        # Style label & canvas
        try:
            self.label.configure(bg=BG, fg=TEXT)
        except Exception:
            pass
        try:
            self.canvas.configure(bg=BG, highlightthickness=0)
        except Exception:
            pass

        # Try to import psutil lazily
        try:
            import psutil  # type: ignore
            self.psutil = psutil
        except Exception:
            self.psutil = None

        # CPU history for bar graph
        self.samples = []        # list of CPU percentages [0..100]
        self.max_samples = 120   # will be recomputed from canvas width

        self._last_update = 0.0
        self._schedule_next()

    # ---------------------------------------------------------
    # Scheduling
    # ---------------------------------------------------------
    def _schedule_next(self):
        # Update ~1x per second
        self.master.after(1000, self.update)

    # ---------------------------------------------------------
    # Main update
    # ---------------------------------------------------------
    def update(self):
        now = time.time()

        cpu = 0.0
        ram = None
        swap = None
        temp = None

        if self.psutil:
            try:
                cpu = float(self.psutil.cpu_percent(interval=None))
            except Exception:
                cpu = 0.0
            try:
                vm = self.psutil.virtual_memory()
                ram = (vm.used / (1024 ** 3), vm.total / (1024 ** 3))
            except Exception:
                ram = None
            try:
                sw = self.psutil.swap_memory()
                swap = (sw.used / (1024 ** 3), sw.total / (1024 ** 3))
            except Exception:
                swap = None
            try:
                temps = self.psutil.sensors_temperatures()
                if temps:
                    # pick first sensor group
                    group = next(iter(temps.values()))
                    if group:
                        temp = group[0].current
            except Exception:
                temp = None

        # Update label text
        label_lines = []
        label_lines.append(f"CPU : {cpu:4.1f}%")
        if ram:
            used, total = ram
            label_lines.append(f"RAM : {used:4.1f} / {total:4.1f} GB")
        if swap:
            used, total = swap
            label_lines.append(f"SWAP: {used:4.1f} / {total:4.1f} GB")
        if temp is not None:
            label_lines.append(f"TEMP: {temp:4.1f} °C")
        else:
            label_lines.append("TEMP: n/a")

        try:
            self.label.configure(text="\n".join(label_lines))
        except Exception:
            pass

        # Add CPU sample & draw bars
        self._add_sample(cpu)
        self._draw_bars()

        self._last_update = now
        self._schedule_next()

    # ---------------------------------------------------------
    # CPU history
    # ---------------------------------------------------------
    def _add_sample(self, value: float):
        self.samples.append(max(0.0, min(100.0, value)))
        # max_samples depends on canvas width; compute lazily
        try:
            w = int(self.canvas.winfo_width())
        except Exception:
            w = 0
        bar_width = 2
        spacing = 2
        if w > 0:
            self.max_samples = max(5, w // (bar_width + spacing))
        else:
            self.max_samples = 120

        if len(self.samples) > self.max_samples:
            self.samples = self.samples[-self.max_samples :]

    # ---------------------------------------------------------
    # Drawing
    # ---------------------------------------------------------
    def _draw_bars(self):
        c = self.canvas
        try:
            c.delete("all")
        except Exception:
            return

        try:
            w = int(c.winfo_width())
            h = int(c.winfo_height())
        except Exception:
            return

        if w <= 0 or h <= 0 or not self.samples:
            return

        bar_width = 2      # your choice: "B"
        spacing = 2        # your choice: "spacing 2"
        bottom = h - 2
        max_height = h - 4

        # Right-align: latest sample on the right edge
        n = len(self.samples)
        total_width = n * (bar_width + spacing)
        start_x = max(2, w - total_width)

        x = start_x
        for value in self.samples:
            # value in [0, 100] → height
            height = int((value / 100.0) * max_height)
            top = bottom - height

            c.create_line(
                x, bottom,
                x, top,
                fill=ACCENT,
                width=bar_width
            )
            x += bar_width + spacing

        # optional baseline
        c.create_line(0, bottom + 1, w, bottom + 1, fill="#004050", width=1)

