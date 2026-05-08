"""Scrollable list of investment cards with edit and delete actions."""

from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from finanmind.models.investment_currency_code import InvestmentCurrencyCode
from finanmind.models.investment_entry import InvestmentEntry
from finanmind.services.investment_portfolio_analytics import InvestmentPortfolioAnalytics
from finanmind.services.investment_service import InvestmentService
from finanmind.ui.budget_ui_theme import BudgetUiTheme
from finanmind.ui.currency_presenter import CurrencyPresenter
from finanmind.ui.percentage_presenter import PercentagePresenter
from finanmind.ui.usd_amount_presenter import UsdAmountPresenter


class InvestmentListPanel:
    """Renders holdings as minimal cards inside a scroll region."""

    def __init__(
        self,
        parent: ctk.CTkFrame,
        service: InvestmentService,
        on_edit: Callable[[str], None],
        on_delete: Callable[[str], None],
    ) -> None:
        self._parent = parent
        self._service = service
        self._on_edit = on_edit
        self._on_delete = on_delete
        self._scroll: ctk.CTkScrollableFrame | None = None

    def attach(self) -> None:
        """Create the scroll host that fills the left column."""
        self._parent.grid_rowconfigure(0, weight=1)
        self._parent.grid_columnconfigure(0, weight=1)
        scroll = ctk.CTkScrollableFrame(
            self._parent,
            fg_color=BudgetUiTheme.BG_MAIN,
            corner_radius=0,
            scrollbar_button_color=BudgetUiTheme.BORDER,
            scrollbar_button_hover_color=BudgetUiTheme.TXT_TER,
        )
        scroll.grid(row=0, column=0, sticky="nsew")
        self._scroll = scroll

    def refresh(self, analytics: InvestmentPortfolioAnalytics) -> None:
        """Rebuild cards from the latest service snapshot."""
        assert self._scroll is not None
        for child in self._scroll.winfo_children():
            child.destroy()
        entries = self._service.entries_snapshot()
        if not entries:
            self._render_empty()
            return
        for ent in self._ordered_entries(entries):
            self._render_card(ent, analytics)

    def _ordered_entries(self, entries: list[InvestmentEntry]) -> list[InvestmentEntry]:
        return sorted(entries, key=lambda e: (e.invested_date_iso, e.category_id.lower()), reverse=True)

    def _render_empty(self) -> None:
        assert self._scroll is not None
        wrap = ctk.CTkFrame(self._scroll, fg_color="transparent")
        wrap.pack(fill="x", pady=36)
        ctk.CTkLabel(
            wrap,
            text="Sin inversiones registradas",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color=BudgetUiTheme.TXT_PRI,
        ).pack(pady=(0, 6))
        ctk.CTkLabel(
            wrap,
            text="Añade categorías y luego registra montos por categoría.",
            font=ctk.CTkFont(size=12),
            text_color=BudgetUiTheme.TXT_SEC,
        ).pack()

    def _render_card(self, ent: InvestmentEntry, analytics: InvestmentPortfolioAnalytics) -> None:
        assert self._scroll is not None
        card = ctk.CTkFrame(
            self._scroll,
            fg_color=BudgetUiTheme.BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=BudgetUiTheme.BORDER,
        )
        card.pack(fill="x", pady=6)
        self._render_card_header(card, ent, analytics)
        self._render_card_meta(card, ent, analytics)
        self._render_card_actions(card, ent)

    def _render_card_header(self, card: ctk.CTkFrame, ent: InvestmentEntry, analytics: InvestmentPortfolioAnalytics) -> None:
        head = ctk.CTkFrame(card, fg_color="transparent")
        head.pack(fill="x", padx=14, pady=(12, 4))
        title = analytics.category_label_for(ent.category_id)
        ctk.CTkLabel(
            head,
            text=title,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=BudgetUiTheme.TXT_PRI,
        ).pack(side="left")
        share = analytics.share_for_entry(ent)
        pct = PercentagePresenter.format_pct(share * 100.0)
        ctk.CTkLabel(head, text=pct, font=ctk.CTkFont(size=12), text_color=BudgetUiTheme.ACCENT).pack(side="right")

    def _render_card_meta(self, card: ctk.CTkFrame, ent: InvestmentEntry, analytics: InvestmentPortfolioAnalytics) -> None:
        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="x", padx=14, pady=(0, 8))
        row = ctk.CTkFrame(body, fg_color="transparent")
        row.pack(fill="x")
        self._mount_currency_badge(row, ent.currency_code)
        money = self._format_amount(ent)
        ctk.CTkLabel(row, text=money, text_color=BudgetUiTheme.TXT_PRI, font=ctk.CTkFont(size=13, weight="bold")).pack(
            side="left", padx=(6, 0)
        )
        ctk.CTkLabel(row, text=ent.invested_date_iso, text_color=BudgetUiTheme.TXT_TER, font=ctk.CTkFont(size=11)).pack(
            side="right"
        )
        if ent.description.strip():
            self._render_note(body, ent.description.strip())

    def _mount_currency_badge(self, row: ctk.CTkFrame, currency_code: str) -> None:
        ctk.CTkLabel(
            row,
            text=currency_code.upper(),
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=BudgetUiTheme.ACCENT,
            fg_color=BudgetUiTheme.INFO_BG,
            corner_radius=6,
            padx=8,
            pady=2,
        ).pack(side="left")

    def _format_amount(self, ent: InvestmentEntry) -> str:
        if ent.currency_code.upper() == InvestmentCurrencyCode.USD:
            return UsdAmountPresenter.format_usd(ent.amount)
        return CurrencyPresenter.format_cop(ent.amount)

    def _render_note(self, body: ctk.CTkFrame, note: str) -> None:
        clip = note if len(note) <= 120 else f"{note[:117]}…"
        ctk.CTkLabel(
            body,
            text=clip,
            text_color=BudgetUiTheme.TXT_SEC,
            font=ctk.CTkFont(size=11),
            wraplength=420,
            justify="left",
        ).pack(anchor="w", pady=(6, 0))

    def _render_card_actions(self, card: ctk.CTkFrame, ent: InvestmentEntry) -> None:
        foot = ctk.CTkFrame(card, fg_color="transparent")
        foot.pack(fill="x", padx=10, pady=(0, 10))
        ctk.CTkButton(
            foot,
            text="Editar",
            width=76,
            height=28,
            command=lambda i=ent.investment_id: self._on_edit(i),
            fg_color=BudgetUiTheme.BG_MAIN,
            text_color=BudgetUiTheme.TXT_PRI,
            hover_color=BudgetUiTheme.BORDER,
        ).pack(side="right", padx=4)
        ctk.CTkButton(
            foot,
            text="Eliminar",
            width=84,
            height=28,
            fg_color=BudgetUiTheme.RED,
            hover_color="#dc2626",
            command=lambda i=ent.investment_id: self._on_delete(i),
        ).pack(side="right")
