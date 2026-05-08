"""Month selector strip for dashboard filtering."""

from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from finanmind.services.month_label_formatter import MonthLabelFormatter
from finanmind.ui.budget_ui_theme import BudgetUiTheme


class DashboardMonthToolbar:
    """Option menu showing Spanish month labels mapped to ``yyyy-mm`` keys."""

    def __init__(self, parent: ctk.CTkFrame, month_var: ctk.StringVar, on_change: Callable[[], None]) -> None:
        self._parent = parent
        self._month_var = month_var
        self._on_change = on_change
        self._menu: ctk.CTkOptionMenu | None = None
        self._label_to_key: dict[str, str] = {}
        self._suppress_change = False

    def attach(self) -> None:
        """Pack the toolbar row."""
        bar = ctk.CTkFrame(
            self._parent,
            fg_color=BudgetUiTheme.BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=BudgetUiTheme.BORDER,
        )
        bar.pack(fill="x", pady=(0, 10))
        inner = ctk.CTkFrame(bar, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=12)
        self._mount_heading(inner)
        self._mount_menu(inner)

    def set_month_keys(self, keys: list[str], selected: str) -> None:
        """Refresh choices while keeping a valid selection."""
        if not keys:
            return
        labels = [MonthLabelFormatter.spanish_month_year(k) for k in keys]
        self._label_to_key = dict(zip(labels, keys, strict=True))
        pick_key = selected if selected in keys else keys[0]
        pick_label = MonthLabelFormatter.spanish_month_year(pick_key)
        assert self._menu is not None
        self._suppress_change = True
        self._menu.configure(values=labels)
        self._menu.set(pick_label)
        self._month_var.set(pick_key)
        self._suppress_change = False

    def _mount_heading(self, inner: ctk.CTkFrame) -> None:
        ctk.CTkLabel(
            inner,
            text="Mes de análisis",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=BudgetUiTheme.TXT_PRI,
        ).pack(side="left", padx=(0, 12))

    def _mount_menu(self, inner: ctk.CTkFrame) -> None:
        menu = ctk.CTkOptionMenu(
            inner,
            values=["—"],
            command=self._on_menu_pick,
            width=240,
            height=36,
            fg_color=BudgetUiTheme.BG_MAIN,
            button_color=BudgetUiTheme.BORDER,
            button_hover_color=BudgetUiTheme.TXT_TER,
            dropdown_fg_color=BudgetUiTheme.BG_CARD,
            dropdown_hover_color=BudgetUiTheme.BG_HOVER,
            text_color=BudgetUiTheme.TXT_PRI,
            dropdown_text_color=BudgetUiTheme.TXT_PRI,
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        menu.pack(side="left")
        self._menu = menu

    def _on_menu_pick(self, label: str) -> None:
        if self._suppress_change:
            return
        key = self._label_to_key.get(label, label)
        self._month_var.set(key)
        self._on_change()
