"""Titled donut and legend for one investment currency (COP or USD)."""

from __future__ import annotations

import customtkinter as ctk

from finanmind.services.investment_portfolio_analytics import InvestmentPortfolioAnalytics
from finanmind.ui.budget_ui_theme import BudgetUiTheme
from finanmind.ui.investment_chart_legend_panel import InvestmentChartLegendPanel
from finanmind.ui.investment_donut_canvas import InvestmentDonutCanvas


class InvestmentCurrencyChartBlock:
    """Mounts one distribution card: title, donut, and legend for a currency."""

    def __init__(self, parent: ctk.CTkFrame, title: str, currency_code: str) -> None:
        self._parent = parent
        self._title = title
        self._currency_code = currency_code
        self._donut: InvestmentDonutCanvas | None = None
        self._legend: InvestmentChartLegendPanel | None = None

    def attach(self) -> None:
        """Build the nested card once."""
        card = self._make_card()
        self._mount_title(card)
        self._mount_donut(card)
        self._mount_legend(card)

    def refresh(self, analytics: InvestmentPortfolioAnalytics) -> None:
        """Push fresh slices for this currency into the donut and legend."""
        rows = analytics.category_distribution_for(self._currency_code)
        assert self._donut is not None and self._legend is not None
        self._donut.set_slices(rows)
        self._legend.refresh(rows, self._currency_code)

    def _make_card(self) -> ctk.CTkFrame:
        card = ctk.CTkFrame(
            self._parent,
            fg_color=BudgetUiTheme.BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=BudgetUiTheme.BORDER,
        )
        card.pack(fill="x", pady=(0, 12))
        return card

    def _mount_title(self, card: ctk.CTkFrame) -> None:
        ctk.CTkLabel(
            card,
            text=self._title,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=BudgetUiTheme.TXT_PRI,
        ).pack(anchor="w", padx=14, pady=(12, 4))

    def _mount_donut(self, card: ctk.CTkFrame) -> None:
        holder = ctk.CTkFrame(card, fg_color=BudgetUiTheme.BG_CARD)
        holder.pack(fill="x", padx=8, pady=(0, 4))
        donut = InvestmentDonutCanvas(holder)
        donut.attach()
        self._donut = donut

    def _mount_legend(self, card: ctk.CTkFrame) -> None:
        legend = InvestmentChartLegendPanel(card)
        legend.attach()
        self._legend = legend
