"""Read-only ISO date display plus button that opens the calendar dialog."""

from __future__ import annotations

from datetime import date

import customtkinter as ctk

from finanmind.ui.calendar_pick_dialog import CalendarPickDialog


class IsoDatePickerRow:
    """Shows ``YYYY-MM-DD`` and lets the user pick via ``CalendarPickDialog``."""

    def __init__(self, parent: ctk.CTkFrame) -> None:
        self._anchor = parent.winfo_toplevel()
        self._iso = ""
        self._label: ctk.CTkLabel | None = None

    def attach(self, parent: ctk.CTkFrame, initial_iso: str) -> None:
        """Mount widgets below ``parent`` using ``initial_iso`` as seed."""
        token = initial_iso.strip() if initial_iso.strip() else date.today().isoformat()
        self._iso = token
        self._build(parent)

    def _build(self, parent: ctk.CTkFrame) -> None:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(4, 10))
        lbl = ctk.CTkLabel(row, text=self._iso, width=140, anchor="w", font=ctk.CTkFont(size=14))
        lbl.pack(side="left", padx=(0, 10))
        self._label = lbl
        ctk.CTkButton(row, text="Calendario…", width=130, command=self._open_calendar).pack(side="left")

    def _open_calendar(self) -> None:
        parsed = self._parse_iso(self._iso)
        picked = CalendarPickDialog(self._anchor, parsed).show()
        if picked is None:
            return
        self._iso = picked.strip()
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
        """Return the displayed ISO day."""
        return self._iso
