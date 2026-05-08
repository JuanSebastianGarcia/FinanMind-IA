"""Dashboard section comparing budget labels vs CC actuals over time."""

from __future__ import annotations

import customtkinter as ctk

from finanmind.models.financial_dashboard_snapshot import FinancialDashboardSnapshot
from finanmind.models.linked_pair_series import LinkedPairSeries
from finanmind.ui.budget_ui_theme import BudgetUiTheme
from finanmind.ui.currency_presenter import CurrencyPresenter
from finanmind.ui.dashboard_linked_budget_chart import DashboardLinkedBudgetChart
from finanmind.ui.dashboard_linked_budget_palette import DashboardLinkedBudgetPalette


class DashboardLinkedBudgetPanel:
    """Filters, KPI strip, and line chart for budget-vs-card analytics."""

    _ALL_LABEL = "Todas las categorías"
    _SPAN_OPTIONS = ("3 meses", "6 meses", "12 meses")

    def __init__(self, parent: ctk.CTkScrollableFrame) -> None:
        self._parent = parent
        self._cat_var = ctk.StringVar(value=self._ALL_LABEL)
        self._span_var = ctk.StringVar(value="6 meses")
        self._cat_menu: ctk.CTkOptionMenu | None = None
        self._chart: DashboardLinkedBudgetChart | None = None
        self._kpi_host: ctk.CTkScrollableFrame | None = None
        self._series: list[LinkedPairSeries] = []
        self._anchor = ""
        self._cat_label_to_id: dict[str, str] = {self._ALL_LABEL: ""}

    def attach(self) -> None:
        """Build the section card once."""
        card = self._make_card()
        self._mount_subtitle(card)
        self._mount_filter_row(card)
        self._mount_kpi_strip(card)
        self._mount_chart(card)

    def refresh(self, snap: FinancialDashboardSnapshot) -> None:
        """Apply a fresh snapshot to filters, KPIs, and chart."""
        self._series = list(snap.linked_pair_series)
        self._anchor = snap.month_key
        self._refresh_cat_menu()
        self._refresh_kpis(snap.month_key)
        self._redraw_chart()

    def _make_card(self) -> ctk.CTkFrame:
        card = ctk.CTkFrame(
            self._parent,
            fg_color=BudgetUiTheme.BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=BudgetUiTheme.BORDER,
        )
        card.pack(fill="x", pady=10)
        ctk.CTkLabel(
            card,
            text="Presupuesto vs gasto real (tarjeta de crédito)",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=BudgetUiTheme.TXT_PRI,
        ).pack(anchor="w", padx=14, pady=(12, 0))
        return card

    def _mount_subtitle(self, card: ctk.CTkFrame) -> None:
        ctk.CTkLabel(
            card,
            text="Compara cada etiqueta enlazada con su gasto en TC mes a mes y detecta desvíos.",
            text_color=BudgetUiTheme.TXT_TER,
            font=ctk.CTkFont(size=11),
            anchor="w",
        ).pack(fill="x", padx=14, pady=(0, 4))

    def _mount_filter_row(self, card: ctk.CTkFrame) -> None:
        bar = ctk.CTkFrame(card, fg_color="transparent")
        bar.pack(fill="x", padx=14, pady=(0, 8))
        self._mount_cat_filter(bar)
        self._mount_span_filter(bar)

    def _mount_cat_filter(self, bar: ctk.CTkFrame) -> None:
        ctk.CTkLabel(bar, text="Categoría:", text_color=BudgetUiTheme.TXT_SEC).pack(side="left", padx=(0, 6))
        menu = self._build_option_menu(bar, [self._ALL_LABEL], self._on_cat_change, width=240)
        menu.set(self._cat_var.get())
        menu.pack(side="left", padx=(0, 14))
        self._cat_menu = menu

    def _mount_span_filter(self, bar: ctk.CTkFrame) -> None:
        ctk.CTkLabel(bar, text="Rango:", text_color=BudgetUiTheme.TXT_SEC).pack(side="left", padx=(0, 6))
        menu = self._build_option_menu(bar, list(self._SPAN_OPTIONS), self._on_span_change, width=120)
        menu.set(self._span_var.get())
        menu.pack(side="left")

    def _build_option_menu(
        self,
        bar: ctk.CTkFrame,
        values: list[str],
        command,
        width: int,
    ) -> ctk.CTkOptionMenu:
        return ctk.CTkOptionMenu(
            bar,
            values=values,
            command=command,
            width=width,
            height=30,
            fg_color=BudgetUiTheme.BG_MAIN,
            button_color=BudgetUiTheme.BORDER,
            button_hover_color=BudgetUiTheme.TXT_TER,
            dropdown_fg_color=BudgetUiTheme.BG_CARD,
            dropdown_hover_color=BudgetUiTheme.BG_HOVER,
            text_color=BudgetUiTheme.TXT_PRI,
            dropdown_text_color=BudgetUiTheme.TXT_PRI,
        )

    def _mount_kpi_strip(self, card: ctk.CTkFrame) -> None:
        host = ctk.CTkScrollableFrame(
            card,
            fg_color="transparent",
            orientation="horizontal",
            height=124,
        )
        host.pack(fill="x", padx=10, pady=(0, 4))
        self._kpi_host = host

    def _mount_chart(self, card: ctk.CTkFrame) -> None:
        chart = DashboardLinkedBudgetChart(card)
        chart.attach()
        self._chart = chart

    def _on_cat_change(self, label: str) -> None:
        self._cat_var.set(label)
        self._redraw_chart()

    def _on_span_change(self, label: str) -> None:
        self._span_var.set(label)
        self._redraw_chart()

    def _redraw_chart(self) -> None:
        if self._chart is None:
            return
        pid = self._cat_label_to_id.get(self._cat_var.get(), "")
        span = self._span_from_label(self._span_var.get())
        self._chart.set_data(self._series, pid, span, self._anchor)

    def _span_from_label(self, label: str) -> int:
        digits = "".join(ch for ch in label if ch.isdigit())
        return int(digits) if digits else 6

    def _refresh_cat_menu(self) -> None:
        if self._cat_menu is None:
            return
        labels = [self._ALL_LABEL]
        self._cat_label_to_id = {self._ALL_LABEL: ""}
        for s in self._series:
            labels.append(s.label_path)
            self._cat_label_to_id[s.label_path] = s.pair_id
        current = self._cat_var.get() if self._cat_var.get() in labels else self._ALL_LABEL
        self._cat_menu.configure(values=labels)
        self._cat_menu.set(current)
        self._cat_var.set(current)

    def _refresh_kpis(self, anchor: str) -> None:
        if self._kpi_host is None:
            return
        for child in self._kpi_host.winfo_children():
            child.destroy()
        if not self._series:
            self._mount_kpi_empty()
            return
        for idx, s in enumerate(self._series):
            self._mount_kpi_tile(s, anchor, DashboardLinkedBudgetPalette.color_for(idx))

    def _mount_kpi_empty(self) -> None:
        assert self._kpi_host is not None
        ctk.CTkLabel(
            self._kpi_host,
            text="No hay enlaces presupuesto ↔ tarjeta. Crea uno desde una etiqueta o categoría.",
            text_color=BudgetUiTheme.TXT_TER,
            anchor="w",
        ).pack(side="left", padx=8, pady=8)

    def _mount_kpi_tile(self, s: LinkedPairSeries, anchor: str, accent: str) -> None:
        actual = self._actual_for(s, anchor)
        tile = self._make_tile_shell()
        self._fill_tile_header(tile, s, accent)
        self._fill_tile_amounts(tile, s, actual)
        self._fill_tile_delta(tile, s, actual)

    def _make_tile_shell(self) -> ctk.CTkFrame:
        assert self._kpi_host is not None
        tile = ctk.CTkFrame(
            self._kpi_host,
            fg_color=BudgetUiTheme.BG_MAIN,
            corner_radius=10,
            border_width=1,
            border_color=BudgetUiTheme.BORDER,
            width=220,
            height=110,
        )
        tile.pack(side="left", padx=4, pady=2)
        tile.pack_propagate(False)
        return tile

    def _fill_tile_header(self, tile: ctk.CTkFrame, s: LinkedPairSeries, accent: str) -> None:
        ctk.CTkLabel(
            tile,
            text=s.label_path,
            text_color=BudgetUiTheme.TXT_PRI,
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w",
        ).pack(fill="x", padx=10, pady=(8, 0))
        ctk.CTkLabel(
            tile,
            text=f"↪ {s.card_category_path}",
            text_color=accent,
            font=ctk.CTkFont(size=10, weight="bold"),
            anchor="w",
        ).pack(fill="x", padx=10)

    def _fill_tile_amounts(self, tile: ctk.CTkFrame, s: LinkedPairSeries, actual: float) -> None:
        real_cap = f"Real: {CurrencyPresenter.format_cop(actual)}"
        budget_cap = f"Presupuesto: {CurrencyPresenter.format_cop(s.expected_cop)}"
        ctk.CTkLabel(tile, text=real_cap, text_color=BudgetUiTheme.TXT_PRI, anchor="w").pack(fill="x", padx=10, pady=(4, 0))
        ctk.CTkLabel(tile, text=budget_cap, text_color=BudgetUiTheme.TXT_SEC, anchor="w").pack(fill="x", padx=10)

    def _fill_tile_delta(self, tile: ctk.CTkFrame, s: LinkedPairSeries, actual: float) -> None:
        cap, fg = self._delta_caption(s.expected_cop, actual)
        ctk.CTkLabel(
            tile,
            text=cap,
            text_color=fg,
            anchor="w",
            font=ctk.CTkFont(size=11, weight="bold"),
        ).pack(fill="x", padx=10, pady=(2, 8))

    def _delta_caption(self, expected: float, actual: float) -> tuple[str, str]:
        if expected <= 0:
            return "Sin presupuesto definido", BudgetUiTheme.TXT_TER
        if actual <= 0:
            return "Sin gasto este mes", BudgetUiTheme.GREEN
        delta_pct = (actual - expected) / expected * 100.0
        if actual > expected:
            return f"+{delta_pct:.0f}% sobre presupuesto", BudgetUiTheme.RED
        if delta_pct >= -5:
            return f"{delta_pct:.0f}% al límite", BudgetUiTheme.AMBER
        return f"{delta_pct:.0f}% bajo presupuesto", BudgetUiTheme.GREEN

    def _actual_for(self, s: LinkedPairSeries, anchor: str) -> float:
        for m, v in s.points:
            if m == anchor:
                return v
        return 0.0
