"""Color-keyed legend rows aligned with the donut chart slices."""

from __future__ import annotations

import customtkinter as ctk

from finanmind.models.investment_currency_code import InvestmentCurrencyCode
from finanmind.ui.budget_ui_theme import BudgetUiTheme
from finanmind.ui.currency_presenter import CurrencyPresenter
from finanmind.ui.investment_chart_palette import InvestmentChartPalette
from finanmind.ui.percentage_presenter import PercentagePresenter
from finanmind.ui.usd_amount_presenter import UsdAmountPresenter


class InvestmentChartLegendPanel:
    """Maps each slice to a dot, label, percent, and amount (large typography)."""

    def __init__(self, parent: ctk.CTkFrame) -> None:
        self._parent = parent
        self._scroll: ctk.CTkScrollableFrame | None = None

    def attach(self) -> None:
        """Mount a bounded scroll area so the donut keeps space above the table."""
        scroll = ctk.CTkScrollableFrame(
            self._parent,
            fg_color="transparent",
            height=220,
            corner_radius=0,
            scrollbar_button_color=BudgetUiTheme.BORDER,
        )
        scroll.pack(fill="x", expand=False, pady=(6, 0))
        self._scroll = scroll

    def refresh(self, rows: list[tuple[str, float, float]], currency_code: str) -> None:
        """Render one row per ``(label, amount, share)`` tuple."""
        assert self._scroll is not None
        for child in self._scroll.winfo_children():
            child.destroy()
        if not rows:
            self._render_hint()
            return
        for index, row in enumerate(rows):
            self._render_legend_row(index, row, currency_code)

    def _render_hint(self) -> None:
        assert self._scroll is not None
        ctk.CTkLabel(
            self._scroll,
            text="Sin datos para esta moneda",
            text_color=BudgetUiTheme.TXT_TER,
            font=ctk.CTkFont(size=13),
        ).pack(anchor="w", pady=8)

    def _render_legend_row(self, index: int, row: tuple[str, float, float], currency_code: str) -> None:
        assert self._scroll is not None
        label, amount, share = row
        line = ctk.CTkFrame(self._scroll, fg_color="transparent")
        line.pack(fill="x", pady=(0, 10))
        left = ctk.CTkFrame(line, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(
            left,
            text="●",
            text_color=InvestmentChartPalette.color_at(index),
            font=ctk.CTkFont(size=18),
            width=22,
        ).pack(side="left", padx=(0, 6))
        ctk.CTkLabel(
            left,
            text=label,
            text_color=BudgetUiTheme.TXT_PRI,
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w",
        ).pack(side="left", fill="x", expand=True)
        self._mount_value_column(line, amount, share, currency_code)

    def _mount_value_column(self, line: ctk.CTkFrame, amount: float, share: float, currency_code: str) -> None:
        col = ctk.CTkFrame(line, fg_color="transparent")
        col.pack(side="right", padx=(8, 0))
        pct = PercentagePresenter.format_pct(share * 100.0)
        money = self._format_money(amount, currency_code)
        ctk.CTkLabel(
            col,
            text=pct,
            text_color=BudgetUiTheme.ACCENT,
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(anchor="e")
        ctk.CTkLabel(
            col,
            text=money,
            text_color=BudgetUiTheme.TXT_PRI,
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="e")

    def _format_money(self, amount: float, currency_code: str) -> str:
        if currency_code.upper() == InvestmentCurrencyCode.USD:
            return UsdAmountPresenter.format_usd(amount)
        return CurrencyPresenter.format_cop(amount)
