"""Startup window placement — maximize when the platform allows it."""

from __future__ import annotations

import ctypes
import sys

import tkinter as tk


class MainWindowPlacement:
    """Deferred wm tweaks so CustomTkinter does not undo maximize during bootstrap."""

    _SW_SHOWMAXIMIZED = 3

    @classmethod
    def apply_maximized(cls, window: tk.Misc, *, min_width: int = 1000, min_height: int = 620) -> None:
        """Request maximize repeatedly; CTk often resets state until after the first ticks."""
        window.minsize(min_width, min_height)
        cls._schedule_zoom_attempts(window)

    @classmethod
    def _schedule_zoom_attempts(cls, window: tk.Misc) -> None:
        for ms in (0, 1, 25, 120, 350):
            window.after(ms, lambda w=window: cls._attempt_zoom(w))

    @classmethod
    def _attempt_zoom(cls, window: tk.Misc) -> None:
        window.update_idletasks()
        cls._try_state_zoomed(window)
        cls._try_attribute_zoomed(window)
        cls._windows_show_maximized(window)

    @classmethod
    def _try_state_zoomed(cls, window: tk.Misc) -> None:
        try:
            window.state("zoomed")
        except tk.TclError:
            return

    @classmethod
    def _try_attribute_zoomed(cls, window: tk.Misc) -> None:
        try:
            window.attributes("-zoomed", True)
        except tk.TclError:
            return

    @classmethod
    def _windows_show_maximized(cls, window: tk.Misc) -> None:
        if sys.platform != "win32":
            return
        try:
            hwnd = window.winfo_id()
            ctypes.windll.user32.ShowWindow(hwnd, cls._SW_SHOWMAXIMIZED)
        except (OSError, ValueError, tk.TclError):
            return
