"""Section card with a compact donut and COP/USD legend."""

from __future__ import annotations

import customtkinter as ctk

from finanmind.ui.budget_ui_theme import BudgetUiTheme
from finanmind.ui.investment_chart_legend_panel import InvestmentChartLegendPanel
from finanmind.ui.investment_donut_canvas import InvestmentDonutCanvas


class DashboardDonutPanel:
    """Titled donut plus legend for dashboard sections."""

    def __init__(self, parent: ctk.CTkFrame, title: str, donut_size: int = 200, legend_height: int = 140) -> None:
        self._parent = parent
        self._title = title
        self._donut_size = donut_size
        self._legend_height = legend_height
        self._donut: InvestmentDonutCanvas | None = None
        self._legend: InvestmentChartLegendPanel | None = None

    def attach(self) -> None:
        """Mount the bordered card once."""
        card = self._make_shell()
        self._mount_title(card)
        body = ctk.CTkFrame(card, fg_color=BudgetUiTheme.BG_CARD)
        body.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self._mount_donut(body)
        self._mount_legend(card)

    def refresh(self, rows: list[tuple[str, float, float]], currency_code: str) -> None:
        """Update slices for COP or USD legends."""
        assert self._donut is not None and self._legend is not None
        self._donut.set_slices(rows)
        self._legend.refresh(rows, currency_code)

    def _make_shell(self) -> ctk.CTkFrame:
        card = ctk.CTkFrame(
            self._parent,
            fg_color=BudgetUiTheme.BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=BudgetUiTheme.BORDER,
        )
        card.pack(fill="both", expand=True, padx=6, pady=6)
        return card

    def _mount_title(self, card: ctk.CTkFrame) -> None:
        ctk.CTkLabel(
            card,
            text=self._title,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=BudgetUiTheme.TXT_PRI,
        ).pack(anchor="w", padx=14, pady=(12, 4))

    def _mount_donut(self, body: ctk.CTkFrame) -> None:
        holder = ctk.CTkFrame(body, fg_color=BudgetUiTheme.BG_CARD)
        holder.pack(fill="x")
        donut = InvestmentDonutCanvas(holder, size=self._donut_size)
        donut.attach()
        self._donut = donut

    def _mount_legend(self, card: ctk.CTkFrame) -> None:
        legend = InvestmentChartLegendPanel(card, scroll_height=self._legend_height)
        legend.attach()
        self._legend = legend
