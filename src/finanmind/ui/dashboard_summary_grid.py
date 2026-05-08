"""Six KPI tiles for the financial dashboard header."""

from __future__ import annotations

import customtkinter as ctk

from finanmind.models.financial_dashboard_snapshot import FinancialDashboardSnapshot
from finanmind.ui.budget_ui_theme import BudgetUiTheme
from finanmind.ui.currency_presenter import CurrencyPresenter
from finanmind.ui.usd_amount_presenter import UsdAmountPresenter


class DashboardSummaryGrid:
    """Mounts and refreshes the primary numeric summary for one month."""

    def __init__(self, parent: ctk.CTkFrame) -> None:
        self._parent = parent
        self._host: ctk.CTkFrame | None = None
        self._value_labels: list[ctk.CTkLabel] = []
        self._sub_labels: list[ctk.CTkLabel] = []

    def attach(self) -> None:
        """Create a responsive 3×2 grid of KPI cards."""
        host = ctk.CTkFrame(self._parent, fg_color="transparent")
        host.pack(fill="x", pady=(0, 8))
        for col in range(3):
            host.grid_columnconfigure(col, weight=1, uniform="dash_kpi")
        titles = self._titles()
        for idx, title in enumerate(titles):
            self._spawn_card(host, idx, title)
        self._host = host

    def refresh(self, snap: FinancialDashboardSnapshot) -> None:
        """Push formatted currency strings for the active month."""
        spend = snap.distribution_spent_cop + snap.card_spent_month_cop
        lim = snap.card_limit_total_cop
        debt = snap.card_debt_total_cop
        use = (debt / lim * 100.0) if lim > 0 else 0.0
        self._set_cell(0, CurrencyPresenter.format_cop(snap.income_cop), "Ingresos registrados")
        self._set_cell(1, CurrencyPresenter.format_cop(spend), "Presupuesto + tarjetas")
        self._set_cell(2, CurrencyPresenter.format_cop(snap.cash_remainder_cop), "Tras asignar presupuesto")
        self._set_cell(3, CurrencyPresenter.format_cop(debt), f"Uso acumulado ~{use:.0f}% del cupo")
        self._set_cell(
            4,
            CurrencyPresenter.format_cop(snap.investment_cop),
            UsdAmountPresenter.format_usd(snap.investment_usd),
        )
        self._set_cell(5, CurrencyPresenter.format_cop(snap.savings_hint_cop), "Ingresos − asignaciones − TC")

    def _titles(self) -> list[str]:
        return [
            "Ingresos del mes",
            "Gastos del mes",
            "Saldo (asignaciones)",
            "Deuda tarjetas",
            "Inversión",
            "Superávit estimado",
        ]

    def _spawn_card(self, host: ctk.CTkFrame, idx: int, title: str) -> None:
        row, col = divmod(idx, 3)
        card = ctk.CTkFrame(
            host,
            fg_color=BudgetUiTheme.BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=BudgetUiTheme.BORDER,
        )
        card.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")
        ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=BudgetUiTheme.TXT_SEC,
            anchor="w",
        ).pack(anchor="w", padx=12, pady=(10, 2))
        val = ctk.CTkLabel(
            card,
            text="—",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=BudgetUiTheme.TXT_PRI,
            anchor="w",
        )
        val.pack(anchor="w", padx=12, pady=(0, 2))
        sub = ctk.CTkLabel(
            card,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=BudgetUiTheme.TXT_TER,
            anchor="w",
        )
        sub.pack(anchor="w", padx=12, pady=(0, 10))
        self._value_labels.append(val)
        self._sub_labels.append(sub)

    def _set_cell(self, idx: int, value: str, subtitle: str) -> None:
        if 0 <= idx < len(self._value_labels):
            self._value_labels[idx].configure(text=value)
            self._sub_labels[idx].configure(text=subtitle)
