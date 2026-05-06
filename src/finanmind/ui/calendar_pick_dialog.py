"""Modal calendar chooser that returns an ISO date string."""

from __future__ import annotations

import tkinter as tk
from datetime import date

import customtkinter as ctk
from tkcalendar import Calendar


class CalendarPickDialog:
    """Shows a month grid and returns ``YYYY-MM-DD`` when accepted."""

    def __init__(self, master: ctk.Misc, initial: date) -> None:
        self._master = master
        self._initial = initial
        self._result: str | None = None
        self._win: ctk.CTkToplevel | None = None
        self._calendar: Calendar | None = None

    def show(self) -> str | None:
        """Block until the user confirms or cancels."""
        self._open_window()
        assert self._win is not None
        self._master.wait_window(self._win)
        return self._result

    def _open_window(self) -> None:
        win = ctk.CTkToplevel(self._master)
        self._win = win
        win.title("Elegir fecha")
        win.geometry("340x360")
        win.transient(self._master.winfo_toplevel())
        win.grab_set()
        self._mount_calendar(win)
        self._mount_footer(win)

    def _mount_calendar(self, win: ctk.CTkToplevel) -> None:
        holder = tk.Frame(win)
        holder.pack(fill="both", expand=True, padx=8, pady=(12, 8))
        cal = Calendar(
            holder,
            selectmode="day",
            date_pattern="yyyy-mm-dd",
            year=self._initial.year,
            month=self._initial.month,
            day=self._initial.day,
        )
        cal.pack(fill="both", expand=True)
        self._calendar = cal

    def _mount_footer(self, win: ctk.CTkToplevel) -> None:
        footer = ctk.CTkFrame(win, fg_color="#FFFFFF")
        footer.pack(fill="x", padx=14, pady=(0, 14))
        ctk.CTkButton(footer, text="Cancelar", width=110, command=self._cancel).pack(side="right")
        ctk.CTkButton(footer, text="Aceptar", width=110, command=self._confirm).pack(side="right", padx=(0, 10))

    def _confirm(self) -> None:
        assert self._calendar is not None
        self._result = self._calendar.get_date()
        self._close()

    def _cancel(self) -> None:
        self._result = None
        self._close()

    def _close(self) -> None:
        if self._win is not None:
            self._win.destroy()
