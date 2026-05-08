"""Four summary chips for the investments overview header."""

from __future__ import annotations

import customtkinter as ctk

from finanmind.ui.budget_ui_theme import BudgetUiTheme
from finanmind.ui.currency_presenter import CurrencyPresenter
from finanmind.ui.usd_amount_presenter import UsdAmountPresenter


class InvestmentSummaryStrip:
    """Shows totals per currency, line count, and how many categories exist."""

    def __init__(self, parent: ctk.CTkFrame) -> None:
        self._parent = parent
        self._cop_lbl: ctk.CTkLabel | None = None
        self._usd_lbl: ctk.CTkLabel | None = None
        self._inv_lbl: ctk.CTkLabel | None = None
        self._cat_lbl: ctk.CTkLabel | None = None

    def attach(self) -> None:
        """Mount the horizontal strip under the top bar."""
        row = ctk.CTkFrame(self._parent, fg_color="transparent")
        row.pack(fill="x", pady=(0, 10))
        self._cop_lbl = self._add_metric_card(row, "Total en COP")
        self._usd_lbl = self._add_metric_card(row, "Total en USD")
        self._inv_lbl = self._add_metric_card(row, "Inversiones")
        self._cat_lbl = self._add_metric_card(row, "Categorías")

    def refresh(
        self,
        total_cop: float,
        total_usd: float,
        investment_count: int,
        category_count: int,
    ) -> None:
        """Update numbers from analytics."""
        assert self._cop_lbl and self._usd_lbl and self._inv_lbl and self._cat_lbl
        self._cop_lbl.configure(text=CurrencyPresenter.format_cop(total_cop))
        self._usd_lbl.configure(text=UsdAmountPresenter.format_usd(total_usd))
        self._inv_lbl.configure(text=str(investment_count))
        self._cat_lbl.configure(text=str(category_count))

    def _add_metric_card(self, row: ctk.CTkFrame, caption: str) -> ctk.CTkLabel:
        card = ctk.CTkFrame(
            row,
            fg_color=BudgetUiTheme.BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=BudgetUiTheme.BORDER,
        )
        card.pack(side="left", expand=True, fill="both", padx=4)
        ctk.CTkLabel(
            card,
            text=caption,
            text_color=BudgetUiTheme.TXT_SEC,
            font=ctk.CTkFont(size=10),
        ).pack(anchor="w", padx=10, pady=(8, 2))
        val = ctk.CTkLabel(
            card,
            text="—",
            text_color=BudgetUiTheme.TXT_PRI,
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        val.pack(anchor="w", padx=10, pady=(0, 10))
        return val
