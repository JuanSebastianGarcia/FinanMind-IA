"""Owns the credit-cards layer; swaps between dashboard and per-card detail views."""

from __future__ import annotations

import customtkinter as ctk

from finanmind.budget.book_service import BudgetBookService
from finanmind.services.credit_card_service import CreditCardService
from finanmind.ui.budget_ui_theme import BudgetUiTheme
from finanmind.ui.credit_card_detail_window import CreditCardDetailWindow
from finanmind.ui.credit_cards_dashboard_window import CreditCardsDashboardWindow


class CreditCardsRouter:
    """Drives navigation between the cards dashboard and a single card detail view."""

    def __init__(
        self,
        host: ctk.CTkFrame,
        service: CreditCardService,
        *,
        book_service: BudgetBookService | None = None,
    ) -> None:
        self._host = host
        self._service = service
        self._book = book_service
        self._stage: ctk.CTkFrame | None = None
        self._dashboard: CreditCardsDashboardWindow | None = None
        self._current_view = "dashboard"
        self._current_card_id: str = ""

    def attach(self) -> None:
        """Build the inner stage and show the dashboard."""
        stage = ctk.CTkFrame(self._host, fg_color=BudgetUiTheme.BG_MAIN, corner_radius=0)
        stage.pack(fill="both", expand=True)
        self._stage = stage
        self._show_dashboard()

    def refresh(self) -> None:
        """Refresh the visible view from disk-loaded state."""
        if self._current_view == "dashboard":
            self._show_dashboard()
        else:
            self._show_detail(self._current_card_id)

    def _show_dashboard(self) -> None:
        assert self._stage is not None
        self._clear_stage()
        self._current_view = "dashboard"
        self._current_card_id = ""
        dashboard = CreditCardsDashboardWindow(self._stage, self._service, self._on_open_card)
        dashboard.attach()
        self._dashboard = dashboard

    def _show_detail(self, card_id: str) -> None:
        assert self._stage is not None
        self._clear_stage()
        self._current_view = "detail"
        self._current_card_id = card_id
        detail = CreditCardDetailWindow(
            self._stage,
            self._service,
            card_id,
            on_back=self._on_back,
            on_card_deleted=self._on_card_deleted,
            book_service=self._book,
        )
        detail.attach()

    def _clear_stage(self) -> None:
        assert self._stage is not None
        for child in self._stage.winfo_children():
            child.destroy()

    def _on_open_card(self, card_id: str) -> None:
        self._show_detail(card_id)

    def _on_back(self) -> None:
        self._show_dashboard()

    def _on_card_deleted(self) -> None:
        self._show_dashboard()
