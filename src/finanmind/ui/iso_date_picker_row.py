"""Bold date row with Hoy and Cambiar fecha; opens anchored calendar overlay."""

from __future__ import annotations

from datetime import date

import customtkinter as ctk

from finanmind.ui.budget_ui_theme import BudgetUiTheme
from finanmind.ui.calendar_popdown import CalendarPopdown


class IsoDatePickerRow:
    """Date row plus month grid popdown (Spanish UI), aligned under the row."""

    def __init__(self) -> None:
        self._iso = ""
        self._label: ctk.CTkLabel | None = None
        self._row_anchor: ctk.CTkFrame | None = None

    def attach(self, parent: ctk.CTkFrame, initial_iso: str) -> None:
        """Mount under ``parent`` using ``initial_iso`` (or today when empty)."""
        token = initial_iso.strip() if initial_iso.strip() else date.today().isoformat()
        self._iso = token
        self._mount_row(parent)

    def _mount_row(self, parent: ctk.CTkFrame) -> None:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(3, 12))
        self._row_anchor = row
        self._mount_value_label(row)
        self._mount_today_btn(row)
        self._mount_change_btn(row)

    def _mount_value_label(self, row: ctk.CTkFrame) -> None:
        self._label = ctk.CTkLabel(
            row,
            text=self._iso,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=BudgetUiTheme.TXT_PRI,
        )
        self._label.pack(side="left")

    def _mount_today_btn(self, row: ctk.CTkFrame) -> None:
        ctk.CTkButton(
            row,
            text="Hoy",
            command=self._set_today,
            fg_color=BudgetUiTheme.BG_MAIN,
            text_color=BudgetUiTheme.TXT_SEC,
            hover_color=BudgetUiTheme.BORDER,
            corner_radius=6,
            height=26,
            font=ctk.CTkFont(size=11),
            border_width=1,
            border_color=BudgetUiTheme.BORDER,
        ).pack(side="left", padx=8)

    def _mount_change_btn(self, row: ctk.CTkFrame) -> None:
        ctk.CTkButton(
            row,
            text="Calendario ▼",
            command=self._pick_date,
            fg_color="transparent",
            text_color=BudgetUiTheme.ACCENT,
            hover_color=BudgetUiTheme.INFO_BG,
            corner_radius=6,
            height=26,
            font=ctk.CTkFont(size=11),
            border_width=1,
            border_color=BudgetUiTheme.ACCENT,
        ).pack(side="left")

    def _set_today(self) -> None:
        self._iso = date.today().isoformat()
        assert self._label is not None
        self._label.configure(text=self._iso)

    def _pick_date(self) -> None:
        assert self._row_anchor is not None
        cur = self._parse_iso(self._iso)
        CalendarPopdown(self._row_anchor, cur, self._apply_iso).open()

    def _apply_iso(self, iso: str) -> None:
        self._iso = iso.strip()
        assert self._label is not None
        self._label.configure(text=self._iso)

    def _parse_iso(self, raw: str) -> date:
        parts = raw.strip().split("-")
        if len(parts) == 3:
            try:
                return date(int(parts[0]), int(parts[1]), int(parts[2]))
            except ValueError:
                pass
        return date.today()

    def get_iso(self) -> str:
        """Return the current ISO day."""
        return self._iso
