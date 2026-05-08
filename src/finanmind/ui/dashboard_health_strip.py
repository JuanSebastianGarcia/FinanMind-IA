"""Compact status chips for high-level financial health."""

from __future__ import annotations

import customtkinter as ctk

from finanmind.ui.budget_ui_theme import BudgetUiTheme


class DashboardHealthStrip:
    """Maps ``(title, tone)`` tuples to soft badge colors."""

    def __init__(self, parent: ctk.CTkFrame) -> None:
        self._parent = parent
        self._row: ctk.CTkFrame | None = None

    def attach(self) -> None:
        """Create the horizontal host."""
        title = ctk.CTkLabel(
            self._parent,
            text="Estado visual",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=BudgetUiTheme.TXT_PRI,
        )
        title.pack(anchor="w", padx=8, pady=(4, 2))
        row = ctk.CTkFrame(self._parent, fg_color="transparent")
        row.pack(fill="x", padx=6, pady=(0, 8))
        self._row = row

    def refresh(self, rows: list[tuple[str, str]]) -> None:
        """Render one pill per health row."""
        assert self._row is not None
        for child in self._row.winfo_children():
            child.destroy()
        for caption, tone in rows:
            self._pill(caption, tone)

    def _pill(self, caption: str, tone: str) -> None:
        assert self._row is not None
        fg, tx = self._colors(tone)
        chip = ctk.CTkFrame(self._row, fg_color=fg, corner_radius=999)
        chip.pack(side="left", padx=4, pady=4)
        ctk.CTkLabel(chip, text=caption, text_color=tx, font=ctk.CTkFont(size=12, weight="bold")).pack(
            padx=12, pady=6
        )

    def _colors(self, tone: str) -> tuple[str, str]:
        if tone == "bad":
            return BudgetUiTheme.BADGE_WARN_BG, BudgetUiTheme.BADGE_WARN_FG
        if tone == "warn":
            return BudgetUiTheme.BTN_ADD_LABEL_BG, BudgetUiTheme.BTN_ADD_LABEL_FG
        return BudgetUiTheme.BADGE_OK_BG, BudgetUiTheme.BADGE_OK_FG
