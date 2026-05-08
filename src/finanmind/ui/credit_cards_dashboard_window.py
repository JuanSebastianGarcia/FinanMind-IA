"""Credit cards dashboard: cards summary grid plus add-card action."""

from __future__ import annotations

from collections.abc import Callable
from tkinter import messagebox

import customtkinter as ctk

from finanmind.models.credit_card import CreditCard
from finanmind.services.credit_card_balance import CreditCardBalance
from finanmind.services.credit_card_service import CreditCardService
from finanmind.ui.budget_ui_theme import BudgetUiTheme
from finanmind.ui.credit_card_dialog import CreditCardDialog
from finanmind.ui.currency_presenter import CurrencyPresenter
from finanmind.ui.percentage_presenter import PercentagePresenter


class CreditCardsDashboardWindow:
    """Lists every registered card with its debt, available credit, and usage bar."""

    _COLUMNS = 3

    def __init__(
        self,
        host: ctk.CTkFrame,
        service: CreditCardService,
        on_open_card: Callable[[str], None],
    ) -> None:
        self._host = host
        self._service = service
        self._on_open_card = on_open_card
        self._scroll: ctk.CTkScrollableFrame | None = None

    def attach(self) -> None:
        """Build widgets and render the current cards grid."""
        outer = ctk.CTkFrame(self._host, fg_color=BudgetUiTheme.BG_MAIN)
        outer.pack(fill="both", expand=True, padx=20, pady=14)
        self._render_topbar(outer)
        self._render_hint(outer)
        self._mount_grid_region(outer)
        self.refresh()

    def refresh(self) -> None:
        """Re-draw the grid from the service snapshot."""
        assert self._scroll is not None
        self._clear_grid()
        cards = self._service.cards_snapshot()
        if not cards:
            self._render_empty_state()
            return
        for index, card in enumerate(cards):
            self._render_card_tile(card, index)

    def _render_topbar(self, outer: ctk.CTkFrame) -> None:
        bar = self._make_topbar(outer)
        self._populate_topbar(bar)

    def _make_topbar(self, outer: ctk.CTkFrame) -> ctk.CTkFrame:
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

    def _populate_topbar(self, bar: ctk.CTkFrame) -> None:
        self._mount_topbar_title(bar)
        self._mount_topbar_action(bar)

    def _mount_topbar_title(self, bar: ctk.CTkFrame) -> None:
        title = ctk.CTkLabel(
            bar,
            text="Tarjetas de crédito",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=BudgetUiTheme.TXT_PRI,
        )
        title.pack(side="left", padx=20, pady=14)

    def _mount_topbar_action(self, bar: ctk.CTkFrame) -> None:
        ctk.CTkButton(
            bar,
            text="Agregar tarjeta",
            command=self._handle_new_card,
            fg_color=BudgetUiTheme.ACCENT,
            hover_color=BudgetUiTheme.ACCENT_HOVER,
            text_color="#ffffff",
            corner_radius=8,
            font=ctk.CTkFont(size=13),
            height=32,
        ).pack(side="right", padx=20, pady=12)

    def _render_hint(self, outer: ctk.CTkFrame) -> None:
        hint = ctk.CTkLabel(
            outer,
            text="Administra tus tarjetas, sus gastos y pagos por ciclo de facturación.",
            font=ctk.CTkFont(size=12),
            text_color=BudgetUiTheme.TXT_SEC,
        )
        hint.pack(anchor="w", pady=(8, 6))

    def _mount_grid_region(self, outer: ctk.CTkFrame) -> None:
        scroll = ctk.CTkScrollableFrame(
            outer,
            fg_color=BudgetUiTheme.BG_MAIN,
            corner_radius=0,
            scrollbar_button_color=BudgetUiTheme.BORDER,
            scrollbar_button_hover_color=BudgetUiTheme.TXT_TER,
        )
        scroll.pack(fill="both", expand=True)
        for col in range(self._COLUMNS):
            scroll.grid_columnconfigure(col, weight=1, uniform="card_cols")
        self._scroll = scroll

    def _clear_grid(self) -> None:
        assert self._scroll is not None
        for child in self._scroll.winfo_children():
            child.destroy()

    def _render_empty_state(self) -> None:
        assert self._scroll is not None
        wrapper = ctk.CTkFrame(self._scroll, fg_color="transparent")
        wrapper.grid(row=0, column=0, columnspan=self._COLUMNS, sticky="nsew", pady=40)
        ctk.CTkLabel(
            wrapper,
            text="Sin tarjetas registradas",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=BudgetUiTheme.TXT_PRI,
        ).pack(pady=(20, 6))
        ctk.CTkLabel(
            wrapper,
            text="Pulsa “Agregar tarjeta” para comenzar a registrar tus gastos.",
            font=ctk.CTkFont(size=12),
            text_color=BudgetUiTheme.TXT_SEC,
        ).pack()

    def _render_card_tile(self, card: CreditCard, index: int) -> None:
        assert self._scroll is not None
        row, col = divmod(index, self._COLUMNS)
        tile = self._make_tile_frame(self._scroll, card.color)
        tile.grid(row=row, column=col, sticky="nsew", padx=8, pady=8)
        self._populate_tile(tile, card)

    def _make_tile_frame(self, parent: ctk.CTkBaseClass, accent_color: str) -> ctk.CTkFrame:
        tile = ctk.CTkFrame(
            parent,
            fg_color=BudgetUiTheme.BG_CARD,
            corner_radius=14,
            border_width=1,
            border_color=accent_color or BudgetUiTheme.BORDER,
        )
        return tile

    def _populate_tile(self, tile: ctk.CTkFrame, card: CreditCard) -> None:
        self._render_tile_header(tile, card)
        self._render_tile_amounts(tile, card)
        self._render_tile_usage_bar(tile, card)
        self._render_tile_footer(tile, card)
        self._render_tile_action(tile, card)

    def _render_tile_header(self, tile: ctk.CTkFrame, card: CreditCard) -> None:
        head = ctk.CTkFrame(tile, fg_color="transparent")
        head.pack(fill="x", padx=14, pady=(14, 6))
        ctk.CTkLabel(
            head,
            text=card.name,
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=BudgetUiTheme.TXT_PRI,
        ).pack(side="left")
        ctk.CTkLabel(
            head,
            text=f"Cierre día {card.cut_day}",
            font=ctk.CTkFont(size=11),
            text_color=BudgetUiTheme.TXT_SEC,
        ).pack(side="right")

    def _render_tile_amounts(self, tile: ctk.CTkFrame, card: CreditCard) -> None:
        debt = self._debt_for(card)
        avail = CreditCardBalance.available_credit(
            card.limit_cop,
            self._service.expenses_for_card(card.card_id),
            self._service.payments_for_card(card.card_id),
        )
        body = ctk.CTkFrame(tile, fg_color="transparent")
        body.pack(fill="x", padx=14, pady=(0, 6))
        self._render_amount_row(body, "Deuda actual", CurrencyPresenter.format_cop(debt), BudgetUiTheme.TXT_PRI)
        self._render_amount_row(body, "Cupo disponible", CurrencyPresenter.format_cop(avail), BudgetUiTheme.TXT_SEC)

    def _render_amount_row(
        self,
        parent: ctk.CTkFrame,
        caption: str,
        value: str,
        value_color: str,
    ) -> None:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x")
        ctk.CTkLabel(
            row,
            text=caption,
            font=ctk.CTkFont(size=11),
            text_color=BudgetUiTheme.TXT_SEC,
        ).pack(side="left")
        ctk.CTkLabel(
            row,
            text=value,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=value_color,
        ).pack(side="right")

    def _render_tile_usage_bar(self, tile: ctk.CTkFrame, card: CreditCard) -> None:
        ratio = CreditCardBalance.usage_ratio(
            card.limit_cop,
            self._service.expenses_for_card(card.card_id),
            self._service.payments_for_card(card.card_id),
        )
        bar_wrap = ctk.CTkFrame(tile, fg_color="transparent")
        bar_wrap.pack(fill="x", padx=14, pady=(2, 6))
        bar = ctk.CTkProgressBar(bar_wrap, height=8, progress_color=self._tone_for_ratio(ratio))
        bar.set(ratio)
        bar.pack(fill="x")
        caption = f"{PercentagePresenter.format_pct(ratio * 100)} del cupo usado"
        ctk.CTkLabel(
            bar_wrap,
            text=caption,
            font=ctk.CTkFont(size=11),
            text_color=BudgetUiTheme.TXT_TER,
        ).pack(anchor="w", pady=(2, 0))

    def _tone_for_ratio(self, ratio: float) -> str:
        if ratio >= 0.85:
            return BudgetUiTheme.RED
        if ratio >= 0.6:
            return BudgetUiTheme.AMBER
        return BudgetUiTheme.ACCENT

    def _render_tile_footer(self, tile: ctk.CTkFrame, card: CreditCard) -> None:
        ctk.CTkLabel(
            tile,
            text=f"Pago día {card.payment_due_day}  ·  Cupo {CurrencyPresenter.format_cop(card.limit_cop)}",
            font=ctk.CTkFont(size=11),
            text_color=BudgetUiTheme.TXT_TER,
        ).pack(anchor="w", padx=14, pady=(0, 8))

    def _render_tile_action(self, tile: ctk.CTkFrame, card: CreditCard) -> None:
        ctk.CTkButton(
            tile,
            text="Abrir tarjeta",
            command=lambda cid=card.card_id: self._on_open_card(cid),
            fg_color=BudgetUiTheme.ACCENT,
            hover_color=BudgetUiTheme.ACCENT_HOVER,
            text_color="#ffffff",
            corner_radius=8,
            height=32,
            font=ctk.CTkFont(size=12),
        ).pack(fill="x", padx=14, pady=(0, 14))

    def _debt_for(self, card: CreditCard) -> float:
        return CreditCardBalance.outstanding(
            self._service.expenses_for_card(card.card_id),
            self._service.payments_for_card(card.card_id),
        )

    def _handle_new_card(self) -> None:
        dialog = CreditCardDialog(
            self._host.winfo_toplevel(),
            "Nueva tarjeta",
            seed_name="",
            seed_limit=0.0,
            seed_cut_day=15,
            seed_due_day=5,
            seed_color="",
        )
        payload = dialog.show()
        if payload is None:
            return
        self._save_new_card(payload)

    def _save_new_card(self, payload: tuple[str, float, int, int, str]) -> None:
        name, limit, cut_day, due_day, color = payload
        try:
            self._service.add_card(name, limit, cut_day, due_day, color)
        except ValueError as exc:
            messagebox.showwarning("Tarjeta", str(exc))
            return
        self.refresh()
