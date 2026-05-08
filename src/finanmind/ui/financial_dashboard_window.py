"""Cross-domain financial dashboard with month filter and soft visuals."""

from __future__ import annotations

import logging
from tkinter import messagebox

import customtkinter as ctk

from finanmind.budget.book_service import BudgetBookService
from finanmind.models.financial_dashboard_snapshot import FinancialDashboardSnapshot
from finanmind.models.investment_currency_code import InvestmentCurrencyCode
from finanmind.services.credit_card_service import CreditCardService
from finanmind.services.financial_dashboard_service import FinancialDashboardService
from finanmind.services.investment_service import InvestmentService
from finanmind.services.monthly_distribution_service import MonthlyDistributionService
from finanmind.ui.budget_ui_theme import BudgetUiTheme
from finanmind.ui.dashboard_donut_panel import DashboardDonutPanel
from finanmind.ui.dashboard_flow_canvas import DashboardFlowCanvas
from finanmind.ui.dashboard_health_strip import DashboardHealthStrip
from finanmind.ui.dashboard_insights_panel import DashboardInsightsPanel
from finanmind.ui.dashboard_month_toolbar import DashboardMonthToolbar
from finanmind.ui.dashboard_summary_grid import DashboardSummaryGrid
from finanmind.ui.currency_presenter import CurrencyPresenter
from finanmind.ui.usd_amount_presenter import UsdAmountPresenter


class FinancialDashboardWindow:
    """Hosts KPIs, charts, investments, insights, and health for one month."""

    def __init__(
        self,
        host: ctk.CTkFrame,
        book: BudgetBookService,
        ledger: MonthlyDistributionService,
        cards: CreditCardService,
        investments: InvestmentService,
    ) -> None:
        self._host = host
        self._service = FinancialDashboardService(book, ledger, cards, investments)
        self._month_var = ctk.StringVar(value="")
        self._toolbar: DashboardMonthToolbar | None = None
        self._summary: DashboardSummaryGrid | None = None
        self._budget_donut: DashboardDonutPanel | None = None
        self._credit_donut: DashboardDonutPanel | None = None
        self._cc_usage: ctk.CTkLabel | None = None
        self._flow: DashboardFlowCanvas | None = None
        self._inv_cop: DashboardDonutPanel | None = None
        self._inv_usd: DashboardDonutPanel | None = None
        self._inv_note: ctk.CTkLabel | None = None
        self._insights: DashboardInsightsPanel | None = None
        self._health: DashboardHealthStrip | None = None
        self._log = logging.getLogger(__name__)

    def attach(self) -> None:
        """Build layout once."""
        outer = self._make_outer_shell()
        self._mount_title_bar(outer)
        self._toolbar = DashboardMonthToolbar(outer, self._month_var, self.refresh)
        self._toolbar.attach()
        self._summary = DashboardSummaryGrid(outer)
        self._summary.attach()
        self._mount_scroll_area(outer)
        self.refresh()

    def refresh(self) -> None:
        """Reload services are triggered by the shell; rebuild aggregates."""
        try:
            snap = self._service.build_snapshot(self._month_var.get().strip())
        except Exception as exc:
            self._log.exception("Dashboard snapshot failed: %s", exc)
            messagebox.showerror("Finanmind", "No se pudo actualizar el dashboard.")
            return
        self._apply_snapshot(snap)

    def _make_outer_shell(self) -> ctk.CTkFrame:
        outer = ctk.CTkFrame(self._host, fg_color=BudgetUiTheme.BG_MAIN)
        outer.pack(fill="both", expand=True, padx=20, pady=14)
        return outer

    def _mount_title_bar(self, outer: ctk.CTkFrame) -> None:
        bar = ctk.CTkFrame(
            outer,
            fg_color=BudgetUiTheme.BG_CARD,
            corner_radius=0,
            height=52,
            border_width=1,
            border_color=BudgetUiTheme.BORDER,
        )
        bar.pack(fill="x", pady=(0, 4))
        bar.pack_propagate(False)
        ctk.CTkLabel(
            bar,
            text="Dashboard financiero",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=BudgetUiTheme.TXT_PRI,
        ).pack(side="left", padx=18, pady=12)

    def _mount_scroll_area(self, outer: ctk.CTkFrame) -> None:
        sc = ctk.CTkScrollableFrame(outer, fg_color="transparent")
        sc.pack(fill="both", expand=True)
        self._mount_budget_credit_row(sc)
        self._mount_flow_block(sc)
        self._mount_investment_block(sc)
        self._insights = DashboardInsightsPanel(sc)
        self._insights.attach()
        self._health = DashboardHealthStrip(sc)
        self._health.attach()

    def _mount_budget_credit_row(self, sc: ctk.CTkScrollableFrame) -> None:
        split = ctk.CTkFrame(sc, fg_color="transparent")
        split.pack(fill="x", pady=(4, 0))
        left = ctk.CTkFrame(split, fg_color="transparent")
        right = ctk.CTkFrame(split, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=(0, 6))
        right.pack(side="left", fill="both", expand=True, padx=(6, 0))
        self._budget_donut = DashboardDonutPanel(left, "Distribución del presupuesto (asignado)", 200, 130)
        self._budget_donut.attach()
        self._cc_usage = ctk.CTkLabel(right, text="", text_color=BudgetUiTheme.TXT_SEC, anchor="w")
        self._cc_usage.pack(fill="x", padx=10, pady=(0, 4))
        self._credit_donut = DashboardDonutPanel(right, "Gasto en tarjetas por categoría", 200, 130)
        self._credit_donut.attach()

    def _mount_flow_block(self, sc: ctk.CTkScrollableFrame) -> None:
        card = self._section_shell(sc, "Flujo mensual (ingresos vs asignaciones)")
        hint = ctk.CTkLabel(
            card,
            text="Barras azules: ingresos del mes · Barras grises: dinero asignado a etiquetas del presupuesto",
            text_color=BudgetUiTheme.TXT_TER,
            font=ctk.CTkFont(size=11),
            anchor="w",
        )
        hint.pack(fill="x", padx=14, pady=(0, 2))
        self._flow = DashboardFlowCanvas(card)
        self._flow.attach()

    def _mount_investment_block(self, sc: ctk.CTkScrollableFrame) -> None:
        card = self._section_shell(sc, "Inversiones")
        self._inv_note = ctk.CTkLabel(card, text="", text_color=BudgetUiTheme.TXT_SEC, anchor="w")
        self._inv_note.pack(fill="x", padx=12, pady=(0, 4))
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=4, pady=(0, 8))
        left = ctk.CTkFrame(row, fg_color="transparent")
        right = ctk.CTkFrame(row, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=4)
        right.pack(side="left", fill="both", expand=True, padx=4)
        self._inv_cop = DashboardDonutPanel(left, "Distribución COP", 170, 110)
        self._inv_usd = DashboardDonutPanel(right, "Distribución USD", 170, 110)
        self._inv_cop.attach()
        self._inv_usd.attach()

    def _section_shell(self, sc: ctk.CTkScrollableFrame, title: str) -> ctk.CTkFrame:
        card = ctk.CTkFrame(
            sc,
            fg_color=BudgetUiTheme.BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=BudgetUiTheme.BORDER,
        )
        card.pack(fill="x", pady=10)
        ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=BudgetUiTheme.TXT_PRI,
        ).pack(anchor="w", padx=14, pady=(12, 4))
        return card

    def _apply_snapshot(self, snap: FinancialDashboardSnapshot) -> None:
        assert self._toolbar is not None and self._summary is not None
        self._toolbar.set_month_keys(snap.month_picker_keys, snap.month_key)
        self._month_var.set(snap.month_key)
        self._summary.refresh(snap)
        self._refresh_donuts(snap)
        self._refresh_flow(snap)
        self._refresh_investments(snap)
        self._refresh_meta(snap)

    def _refresh_donuts(self, snap: FinancialDashboardSnapshot) -> None:
        assert self._budget_donut is not None and self._credit_donut is not None and self._cc_usage is not None
        self._budget_donut.refresh(snap.budget_distribution_rows, InvestmentCurrencyCode.COP)
        self._credit_donut.refresh(snap.credit_category_rows, InvestmentCurrencyCode.COP)
        lim = snap.card_limit_total_cop
        use = (snap.card_debt_total_cop / lim * 100.0) if lim > 0 else 0.0
        self._cc_usage.configure(
            text=f"Gasto del mes en TC: {CurrencyPresenter.format_cop(snap.card_spent_month_cop)} · Uso acumulado ~{use:.0f}% del cupo total"
        )

    def _refresh_flow(self, snap: FinancialDashboardSnapshot) -> None:
        assert self._flow is not None
        self._flow.set_points(snap.flow_points)

    def _refresh_investments(self, snap: FinancialDashboardSnapshot) -> None:
        assert self._inv_cop is not None and self._inv_usd is not None and self._inv_note is not None
        self._inv_cop.refresh(snap.investment_rows_cop, InvestmentCurrencyCode.COP)
        self._inv_usd.refresh(snap.investment_rows_usd, InvestmentCurrencyCode.USD)
        cop = CurrencyPresenter.format_cop(snap.investment_month_cop)
        usd = UsdAmountPresenter.format_usd(snap.investment_month_usd)
        self._inv_note.configure(text=f"Aportes registrados en {snap.month_label}: {cop} · {usd}")

    def _refresh_meta(self, snap: FinancialDashboardSnapshot) -> None:
        assert self._insights is not None and self._health is not None
        self._insights.refresh(snap.insights)
        self._health.refresh(snap.health_rows)
