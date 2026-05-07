"""Dropdown-style month calendar: anchored under a widget, Spanish UI, dark popdown chrome."""

from __future__ import annotations

import tkinter as tk
from calendar import MONDAY, Calendar
from collections.abc import Callable
from datetime import date

import customtkinter as ctk


class CalendarPopdown:
    """Floating calendar panel; commits ``YYYY-MM-DD`` or closes without changes."""

    _active: CalendarPopdown | None = None

    _MONTHS_ES = (
        "enero",
        "febrero",
        "marzo",
        "abril",
        "mayo",
        "junio",
        "julio",
        "agosto",
        "septiembre",
        "octubre",
        "noviembre",
        "diciembre",
    )
    _DAY_HDR: tuple[str, ...] = ("LU", "MA", "MI", "JU", "VI", "SA", "DO")

    BG = "#2b2f36"
    SURFACE = "#353a42"
    TXT = "#f3f4f6"
    TXT_MUTED = "#5c6370"
    ACCENT = "#4f8ef7"
    SELECT_BG = "#4f8ef7"
    BORDER = "#1f2329"

    def __init__(
        self,
        anchor: ctk.Misc,
        initial: date,
        on_commit: Callable[[str], None],
    ) -> None:
        self._anchor = anchor
        self._on_commit = on_commit
        self._view = date(initial.year, initial.month, 1)
        self._selected = initial
        self._win: ctk.CTkToplevel | None = None
        self._shell: ctk.CTkFrame | None = None
        self._title_lbl: ctk.CTkLabel | None = None
        self._grid_host: ctk.CTkFrame | None = None

    def open(self) -> None:
        """Show the overlay below ``anchor``."""
        self._retire_previous()
        CalendarPopdown._active = self
        self._spawn_shell()
        self._layout_chrome()
        self._bind_escape()
        self._lift_and_focus()

    def _retire_previous(self) -> None:
        prev = CalendarPopdown._active
        if prev is not None and prev is not self:
            prev._close()

    def _spawn_shell(self) -> None:
        root = self._anchor.winfo_toplevel()
        win = ctk.CTkToplevel(root)
        self._win = win
        win.overrideredirect(True)
        win.configure(fg_color=self.BG)
        try:
            win.attributes("-topmost", True)
        except tk.TclError:
            pass
        shell = ctk.CTkFrame(
            win,
            fg_color=self.BG,
            corner_radius=10,
            border_width=1,
            border_color=self.BORDER,
        )
        shell.pack(fill="both", expand=True, padx=2, pady=2)
        self._shell = shell

    def _layout_chrome(self) -> None:
        assert self._shell is not None
        self._render_header(self._shell)
        self._render_week_row(self._shell)
        self._grid_host = ctk.CTkFrame(self._shell, fg_color="transparent")
        self._grid_host.pack(fill="both", expand=True, padx=6, pady=(0, 4))
        self._refresh_grid()
        self._render_footer(self._shell)
        self._apply_geometry()

    def _render_header(self, shell: ctk.CTkFrame) -> None:
        row = ctk.CTkFrame(shell, fg_color="transparent")
        row.pack(fill="x", padx=6, pady=(8, 4))
        self._nav_btn(row, "‹", self._prev_month).pack(side="left")
        title = ctk.CTkLabel(
            row,
            text=self._month_title(),
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=self.TXT,
        )
        title.pack(side="left", expand=True)
        self._title_lbl = title
        self._nav_btn(row, "›", self._next_month).pack(side="right")

    def _month_title(self) -> str:
        m, y = self._view.month, self._view.year
        return f"{self._MONTHS_ES[m - 1]} de {y}"

    def _nav_btn(self, row: ctk.CTkFrame, text: str, cmd: Callable[[], None]) -> ctk.CTkButton:
        return ctk.CTkButton(
            row,
            text=text,
            width=28,
            height=28,
            command=cmd,
            fg_color=self.SURFACE,
            hover_color=self.BORDER,
            text_color=self.ACCENT,
            font=ctk.CTkFont(size=14),
        )

    def _refresh_header_title(self) -> None:
        if self._title_lbl is not None:
            self._title_lbl.configure(text=self._month_title())

    def _prev_month(self) -> None:
        y, m = self._view.year, self._view.month
        if m == 1:
            y, m = y - 1, 12
        else:
            m -= 1
        self._view = date(y, m, 1)
        self._refresh_header_title()
        self._refresh_grid()

    def _next_month(self) -> None:
        y, m = self._view.year, self._view.month
        if m == 12:
            y, m = y + 1, 1
        else:
            m += 1
        self._view = date(y, m, 1)
        self._refresh_header_title()
        self._refresh_grid()

    def _render_week_row(self, shell: ctk.CTkFrame) -> None:
        row = ctk.CTkFrame(shell, fg_color="transparent")
        row.pack(fill="x", padx=6, pady=(0, 2))
        for label in self._DAY_HDR:
            ctk.CTkLabel(
                row,
                text=label,
                width=32,
                font=ctk.CTkFont(size=10),
                text_color=self.TXT_MUTED,
            ).pack(side="left", padx=2)

    def _refresh_grid(self) -> None:
        assert self._grid_host is not None
        for child in self._grid_host.winfo_children():
            child.destroy()
        cal = Calendar(firstweekday=MONDAY)
        weeks = cal.monthdatescalendar(self._view.year, self._view.month)
        for week in weeks:
            self._render_week_slots(week)

    def _render_week_slots(self, week: list[date]) -> None:
        assert self._grid_host is not None
        row = ctk.CTkFrame(self._grid_host, fg_color="transparent")
        row.pack(fill="x", pady=1)
        for day in week:
            self._day_cell(row, day).pack(side="left", padx=2, pady=1)

    def _day_cell(self, row: ctk.CTkFrame, day: date) -> ctk.CTkButton:
        in_month = day.month == self._view.month
        is_sel = day == self._selected
        fg = self.SELECT_BG if is_sel else self.SURFACE
        tx = "#ffffff" if is_sel else (self.TXT if in_month else self.TXT_MUTED)
        return ctk.CTkButton(
            row,
            text=str(day.day),
            width=32,
            height=28,
            command=lambda d=day: self._pick_day(d),
            fg_color=fg,
            hover_color=self.ACCENT if not is_sel else self.SELECT_BG,
            text_color=tx,
            font=ctk.CTkFont(size=12),
            corner_radius=4,
        )

    def _pick_day(self, day: date) -> None:
        self._selected = day
        self._on_commit(day.isoformat())
        self._close()

    def _render_footer(self, shell: ctk.CTkFrame) -> None:
        row = ctk.CTkFrame(shell, fg_color="transparent")
        row.pack(fill="x", padx=8, pady=(4, 8))
        self._text_btn(row, "Borrar", self._dismiss).pack(side="left")
        self._text_btn(row, "Hoy", self._pick_today).pack(side="right")

    def _text_btn(self, row: ctk.CTkFrame, text: str, cmd: Callable[[], None]) -> ctk.CTkButton:
        return ctk.CTkButton(
            row,
            text=text,
            command=cmd,
            fg_color="transparent",
            hover_color=self.SURFACE,
            text_color=self.ACCENT,
            font=ctk.CTkFont(size=12),
            width=72,
            height=26,
        )

    def _pick_today(self) -> None:
        self._on_commit(date.today().isoformat())
        self._close()

    def _dismiss(self) -> None:
        self._close()

    def _close(self) -> None:
        if CalendarPopdown._active is self:
            CalendarPopdown._active = None
        if self._win is not None:
            try:
                self._win.grab_release()
            except tk.TclError:
                pass
            self._win.destroy()
        self._win = None

    def _apply_geometry(self) -> None:
        assert self._win is not None
        self._anchor.update_idletasks()
        self._win.update_idletasks()
        x = self._anchor.winfo_rootx()
        y = self._anchor.winfo_rooty() + self._anchor.winfo_height()
        w = max(self._win.winfo_reqwidth(), 276)
        h = max(self._win.winfo_reqheight(), 280)
        self._win.geometry(f"{int(w)}x{int(h)}+{int(x)}+{int(y)}")

    def _bind_escape(self) -> None:
        assert self._win is not None

        def esc(_e: object) -> str:
            self._dismiss()
            return "break"

        self._win.bind("<Escape>", esc)

    def _lift_and_focus(self) -> None:
        assert self._win is not None
        self._win.grab_set()
        self._win.lift()
        self._win.focus_force()
