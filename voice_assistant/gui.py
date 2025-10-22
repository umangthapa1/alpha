"""Simple Iron-Man-like HUD GUI for Alpha voice assistant.

Runs a Tkinter window in a background thread and accepts thread-safe updates
via a queue. No external dependencies required.
"""
from __future__ import annotations

import threading
import queue
import time
import tkinter as tk
from tkinter import scrolledtext
from typing import Callable, Optional

# Load theme from config if available
try:
    from .config import GUI_THEME, GUI_THEMES
except Exception:
    try:
        from config import GUI_THEME, GUI_THEMES
    except Exception:
        GUI_THEME = "default"
        GUI_THEMES = {
            "default": {
                "bg": "#071020",
                "accent": "#00ffcc",
                "accent_alt": "#9be7ff",
                "secondary": "#9be7ff",
                "canvas_bg": "#0b1a2b",
                "text": "#a7f0ff",
                "title": "#00ffcc",
                "font": "Segoe UI"
            }
        }

# Choose theme values
_THEME = GUI_THEMES.get(GUI_THEME, GUI_THEMES.get("default", list(GUI_THEMES.values())[0]))
_BG = _THEME.get("bg", "#071020")
_ACCENT = _THEME.get("accent", "#00ffcc")
_ACCENT_ALT = _THEME.get("accent_alt", "#9be7ff")
_SECONDARY = _THEME.get("secondary", "#9be7ff")
_CANVAS_BG = _THEME.get("canvas_bg", "#0b1a2b")
_TEXT = _THEME.get("text", "#a7f0ff")
_TITLE = _THEME.get("title", _ACCENT)
_FONT = _THEME.get("font", "Segoe UI")


class AlphaGUI:
    def __init__(self, on_quit: Optional[Callable[[], None]] = None) -> None:
        self._on_quit = on_quit
        self._q: "queue.Queue[tuple[str, object]]" = queue.Queue()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._started = False

    def start(self) -> None:
        if not self._started:
            self._started = True
            self._thread.start()

    def _run(self) -> None:
        # Build UI on this thread
        self.root = tk.Tk()
        self.root.title("Alpha — HUD")
        self.root.configure(bg=_BG)
        self.root.geometry("720x420")

        # Top title
        title = tk.Label(self.root, text="ALPHA", fg=_TITLE, bg=_BG,
                         font=(_FONT, 28, "bold"))
        title.pack(pady=(12, 0))

        # Status label
        self.status_var = tk.StringVar(value="Status: Initializing...")
        status = tk.Label(self.root, textvariable=self.status_var, fg=_SECONDARY,
                          bg=_BG, font=(_FONT, 12))
        status.pack(pady=(4, 8))

        # Canvas for simple animated HUD (bars)
        self.canvas = tk.Canvas(self.root, width=680, height=100, bg=_CANVAS_BG, highlightthickness=0)
        self.canvas.pack(padx=20)
        self._bars = []
        for i in range(20):
            x0 = 10 + i * 33
            rect = self.canvas.create_rectangle(x0, 60, x0 + 20, 100, fill=_ACCENT, outline="")
            self._bars.append(rect)

        # Scrolled text area for transcripts
        self.log = scrolledtext.ScrolledText(self.root, height=8, bg=_CANVAS_BG, fg=_TEXT,
                                             insertbackground=_TEXT, font=("Consolas", 10))
        self.log.pack(fill="both", expand=True, padx=12, pady=10)
        self.log.insert(tk.END, "Alpha HUD started.\n")
        self.log.configure(state=tk.DISABLED)

        # Quit button
        btn_frame = tk.Frame(self.root, bg=_BG)
        btn_frame.pack(pady=(0, 8))
        stop_btn = tk.Button(btn_frame, text="Quit Alpha", command=self._on_quit_clicked,
                             bg=_CANVAS_BG, fg=_TEXT)
        stop_btn.pack()

        # Start periodic handlers
        self._anim_phase = 0.0
        self._tick()
        self._process_queue()

        # Ensure on-close triggers callback
        self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)

        # Enter mainloop (blocks this thread)
        try:
            self.root.mainloop()
        finally:
            # Clean shutdown
            if self._on_quit:
                try:
                    self._on_quit()
                except Exception:
                    pass

    def _on_window_close(self) -> None:
        # Close window and call quit callback
        try:
            self.root.destroy()
        except Exception:
            pass
        if self._on_quit:
            self._on_quit()

    def _on_quit_clicked(self) -> None:
        self._on_window_close()

    def _tick(self) -> None:
        # Animate bars with a pulsing effect dependent on a phase variable
        import math
        self._anim_phase += 0.12
        for i, rect in enumerate(self._bars):
            height = 20 + (math.sin(self._anim_phase + i * 0.35) + 1) * 35
            x0, y0, x1, y1 = self.canvas.coords(rect)
            self.canvas.coords(rect, x0, 100 - height, x1, 100)
            # color ramp
            intensity = int(40 + (math.sin(self._anim_phase + i * 0.35) + 1) * 80)
            # blend between accent and accent_alt for dynamic color
            try:
                # simple blend by interpolation on hex channels
                a_r = int(_ACCENT.lstrip('#')[0:2], 16)
                a_g = int(_ACCENT.lstrip('#')[2:4], 16)
                a_b = int(_ACCENT.lstrip('#')[4:6], 16)
                b_r = int(_ACCENT_ALT.lstrip('#')[0:2], 16)
                b_g = int(_ACCENT_ALT.lstrip('#')[2:4], 16)
                b_b = int(_ACCENT_ALT.lstrip('#')[4:6], 16)
                t = (math.sin(self._anim_phase + i * 0.35) + 1) / 2.0
                r = int(a_r * (1 - t) + b_r * t)
                g = int(a_g * (1 - t) + b_g * t)
                b = int(a_b * (1 - t) + b_b * t)
                color = f"#{r:02x}{g:02x}{b:02x}"
            except Exception:
                color = f"#{intensity:02x}{200:02x}{220:02x}"
            try:
                self.canvas.itemconfig(rect, fill=color)
            except Exception:
                pass

        # schedule next frame
        self.root.after(60, self._tick)

    def _process_queue(self) -> None:
        # Drain queue and apply updates to UI
        try:
            while True:
                kind, payload = self._q.get_nowait()
                if kind == "status":
                    self.status_var.set(payload)
                elif kind == "log":
                    self._append_log(payload)
                elif kind == "listening":
                    if payload:
                        self.status_var.set("Status: Listening... (wake word detected)")
                    else:
                        self.status_var.set("Status: Idle")
        except queue.Empty:
            pass

        # schedule next check
        self.root.after(150, self._process_queue)

    def _append_log(self, text: str) -> None:
        try:
            self.log.configure(state=tk.NORMAL)
            timestamp = time.strftime("%H:%M:%S")
            self.log.insert(tk.END, f"[{timestamp}] {text}\n")
            self.log.see(tk.END)
            self.log.configure(state=tk.DISABLED)
        except Exception:
            pass

    # Thread-safe public APIs
    def update_status(self, text: str) -> None:
        self._q.put(("status", text))

    def log_text(self, text: str) -> None:
        self._q.put(("log", text))

    def set_listening(self, listening: bool) -> None:
        self._q.put(("listening", listening))

    def stop(self) -> None:
        # Close the window from outside thread
        try:
            if hasattr(self, "root"):
                self.root.after(0, self.root.destroy)
        except Exception:
            pass
