"""Investments overview: holdings list, summary metrics, and donut distribution."""

from __future__ import annotations

import logging
from tkinter import messagebox

import customtkinter as ctk

from finanmind.models.investment_currency_code import InvestmentCurrencyCode
from finanmind.services.investment_portfolio_analytics import InvestmentPortfolioAnalytics
from finanmind.services.investment_service import InvestmentService
from finanmind.ui.budget_ui_theme import BudgetUiTheme
from finanmind.ui.investment_categories_manager_dialog import InvestmentCategoriesManagerDialog
from finanmind.ui.investment_currency_chart_block import InvestmentCurrencyChartBlock
from finanmind.ui.investment_entry_editor_dialog import InvestmentEntryEditorDialog
from finanmind.ui.investment_list_panel import InvestmentListPanel
from finanmind.ui.investment_review_dialog import InvestmentReviewDialog
from finanmind.ui.investment_summary_strip import InvestmentSummaryStrip


class InvestmentManagementWindow:
    """Coordinates the investments UI backed by ``InvestmentService``."""

    def __init__(self, host: ctk.CTkFrame, service: InvestmentService) -> None:
        self._host = host
        self._service = service
        self._log = logging.getLogger(__name__)
        self._strip: InvestmentSummaryStrip | None = None
        self._list_panel: InvestmentListPanel | None = None
        self._cop_block: InvestmentCurrencyChartBlock | None = None
        self._usd_block: InvestmentCurrencyChartBlock | None = None

    def attach(self) -> None:
        """Build the layout once."""
        outer = ctk.CTkFrame(self._host, fg_color=BudgetUiTheme.BG_MAIN)
        outer.pack(fill="both", expand=True, padx=20, pady=14)
        self._mount_topbar(outer)
        self._mount_hint(outer)
        self._mount_summary(outer)
        self._mount_body(outer)
        self.refresh()

    def refresh(self) -> None:
        """Reload every widget from the in-memory service snapshot."""
        analytics = self._analytics()
        self._refresh_summary(analytics)
        self._refresh_list(analytics)
        self._refresh_charts(analytics)

    def _toplevel(self) -> ctk.Misc:
        return self._host.winfo_toplevel()

    def _analytics(self) -> InvestmentPortfolioAnalytics:
        return InvestmentPortfolioAnalytics(
            self._service.entries_snapshot(),
            self._service.categories_snapshot(),
        )

    def _refresh_summary(self, analytics: InvestmentPortfolioAnalytics) -> None:
        assert self._strip is not None
        self._strip.refresh(
            analytics.total_for_currency(InvestmentCurrencyCode.COP),
            analytics.total_for_currency(InvestmentCurrencyCode.USD),
            analytics.entry_count(),
            analytics.defined_category_count(),
        )

    def _refresh_list(self, analytics: InvestmentPortfolioAnalytics) -> None:
        assert self._list_panel is not None
        self._list_panel.refresh(analytics)

    def _refresh_charts(self, analytics: InvestmentPortfolioAnalytics) -> None:
        assert self._cop_block is not None and self._usd_block is not None
        self._cop_block.refresh(analytics)
        self._usd_block.refresh(analytics)

    def _mount_topbar(self, outer: ctk.CTkFrame) -> None:
        bar = self._make_topbar_shell(outer)
        self._mount_topbar_title(bar)
        self._mount_topbar_buttons(bar)

    def _make_topbar_shell(self, outer: ctk.CTkFrame) -> ctk.CTkFrame:
        bar = ctk.CTkFrame(
            outer,
            fg_color=BudgetUiTheme.BG_CARD,
            corner_radius=0,
            height=56,
            border_width=1,
            border_color=BudgetUiTheme.BORDER,
        )
        bar.pack(fill="x", pady=(0, 4))
        bar.pack_propagate(False)
        return bar

    def _mount_topbar_title(self, bar: ctk.CTkFrame) -> None:
        ctk.CTkLabel(
            bar,
            text="Gestión de inversiones",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=BudgetUiTheme.TXT_PRI,
        ).pack(side="left", padx=20, pady=14)

    def _mount_topbar_buttons(self, bar: ctk.CTkFrame) -> None:
        self._mount_new_entry_button(bar)
        self._mount_ia_review_button(bar)
        self._mount_categories_button(bar)

    def _mount_new_entry_button(self, bar: ctk.CTkFrame) -> None:
        ctk.CTkButton(
            bar,
            text="Nueva inversión",
            command=self._open_new_entry,
            fg_color=BudgetUiTheme.ACCENT,
            hover_color=BudgetUiTheme.ACCENT_HOVER,
            text_color="#ffffff",
            height=32,
        ).pack(side="right", padx=20, pady=12)

    def _mount_ia_review_button(self, bar: ctk.CTkFrame) -> None:
        ctk.CTkButton(
            bar,
            text="Análisis IA",
            command=self._open_ia_review,
            fg_color=BudgetUiTheme.BG_MAIN,
            text_color=BudgetUiTheme.ACCENT,
            hover_color=BudgetUiTheme.BORDER,
            border_color=BudgetUiTheme.ACCENT,
            border_width=1,
            height=32,
        ).pack(side="right", padx=(0, 10), pady=12)

    def _mount_categories_button(self, bar: ctk.CTkFrame) -> None:
        ctk.CTkButton(
            bar,
            text="Categorías",
            command=self._open_categories,
            fg_color=BudgetUiTheme.BG_MAIN,
            text_color=BudgetUiTheme.TXT_PRI,
            hover_color=BudgetUiTheme.BORDER,
            height=32,
        ).pack(side="right", padx=(0, 10), pady=12)

    def _mount_hint(self, outer: ctk.CTkFrame) -> None:
        ctk.CTkLabel(
            outer,
            text="Define categorías (nombre = activo); cada inversión usa una categoría y moneda COP o USD.",
            font=ctk.CTkFont(size=12),
            text_color=BudgetUiTheme.TXT_SEC,
        ).pack(anchor="w", pady=(6, 8))

    def _mount_summary(self, outer: ctk.CTkFrame) -> None:
        strip = InvestmentSummaryStrip(outer)
        strip.attach()
        self._strip = strip

    def _mount_body(self, outer: ctk.CTkFrame) -> None:
        split = ctk.CTkFrame(outer, fg_color="transparent")
        split.pack(fill="both", expand=True)
        split.grid_columnconfigure(0, weight=3, uniform="inv_cols")
        split.grid_columnconfigure(1, weight=2, uniform="inv_cols")
        split.grid_rowconfigure(0, weight=1)
        left = ctk.CTkFrame(split, fg_color="transparent")
        right = ctk.CTkFrame(split, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_rowconfigure(0, weight=1)
        right.grid_columnconfigure(0, weight=1)
        self._mount_list_column(left)
        self._mount_chart_column(right)

    def _mount_list_column(self, left: ctk.CTkFrame) -> None:
        panel = InvestmentListPanel(left, self._service, self._handle_edit, self._handle_delete)
        panel.attach()
        self._list_panel = panel

    def _mount_chart_column(self, right: ctk.CTkFrame) -> None:
        host = ctk.CTkScrollableFrame(
            right,
            fg_color=BudgetUiTheme.BG_MAIN,
            corner_radius=0,
            scrollbar_button_color=BudgetUiTheme.BORDER,
            scrollbar_button_hover_color=BudgetUiTheme.TXT_TER,
        )
        host.grid(row=0, column=0, sticky="nsew")
        cop = InvestmentCurrencyChartBlock(host, "Distribución en COP por categoría", InvestmentCurrencyCode.COP)
        cop.attach()
        usd = InvestmentCurrencyChartBlock(host, "Distribución en USD por categoría", InvestmentCurrencyCode.USD)
        usd.attach()
        self._cop_block = cop
        self._usd_block = usd

    def _open_categories(self) -> None:
        dlg = InvestmentCategoriesManagerDialog(self._toplevel(), self._service)
        dlg.show()
        self.refresh()

    def _open_ia_review(self) -> None:
        dlg = InvestmentReviewDialog(self._toplevel(), self._service)
        dlg.show()

    def _open_new_entry(self) -> None:
        if not self._service.categories_snapshot():
            messagebox.showinfo("Finanmind", "Crea primero al menos una categoría.")
            return
        dlg = InvestmentEntryEditorDialog(self._toplevel(), self._service, None)
        dlg.show()
        self.refresh()

    def _handle_edit(self, investment_id: str) -> None:
        try:
            ent = self._service.entry_by_id(investment_id)
        except KeyError:
            messagebox.showerror("Finanmind", "No se encontró la inversión.")
            return
        dlg = InvestmentEntryEditorDialog(self._toplevel(), self._service, ent)
        dlg.show()
        self.refresh()

    def _handle_delete(self, investment_id: str) -> None:
        if not messagebox.askyesno("Finanmind", "¿Eliminar esta inversión?"):
            return
        try:
            self._service.delete_entry(investment_id)
        except KeyError:
            messagebox.showerror("Finanmind", "No se encontró la inversión.")
            return
        except RuntimeError as exc:
            self._log.exception("Delete investment persistence failed")
            messagebox.showerror("Finanmind", str(exc))
            return
        self.refresh()
