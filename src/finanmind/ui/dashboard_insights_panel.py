"""Soft list of auto-generated finance insights."""

from __future__ import annotations

import customtkinter as ctk

from finanmind.ui.budget_ui_theme import BudgetUiTheme


class DashboardInsightsPanel:
    """Renders short textual insights without overwhelming the layout."""

    def __init__(self, parent: ctk.CTkFrame) -> None:
        self._parent = parent
        self._body: ctk.CTkFrame | None = None

    def attach(self) -> None:
        """Mount the framed block once."""
        shell = ctk.CTkFrame(
            self._parent,
            fg_color=BudgetUiTheme.INFO_BG,
            corner_radius=12,
            border_width=1,
            border_color=BudgetUiTheme.BORDER,
        )
        shell.pack(fill="x", padx=6, pady=8)
        ctk.CTkLabel(
            shell,
            text="Insights automáticos",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=BudgetUiTheme.TXT_PRI,
        ).pack(anchor="w", padx=14, pady=(12, 4))
        body = ctk.CTkFrame(shell, fg_color="transparent")
        body.pack(fill="x", padx=10, pady=(0, 12))
        self._body = body

    def refresh(self, lines: list[str]) -> None:
        """Replace insight rows."""
        assert self._body is not None
        for child in self._body.winfo_children():
            child.destroy()
        if not lines:
            self._empty_state()
            return
        for line in lines:
            self._add_line(line)

    def _empty_state(self) -> None:
        assert self._body is not None
        ctk.CTkLabel(
            self._body,
            text="Cuando haya más historia mensual aparecerán comparaciones aquí.",
            text_color=BudgetUiTheme.TXT_SEC,
            font=ctk.CTkFont(size=12),
            anchor="w",
        ).pack(anchor="w", pady=4)

    def _add_line(self, text: str) -> None:
        assert self._body is not None
        ctk.CTkLabel(
            self._body,
            text=f"• {text}",
            text_color=BudgetUiTheme.TXT_PRI,
            font=ctk.CTkFont(size=12),
            anchor="w",
            justify="left",
        ).pack(anchor="w", pady=3)
