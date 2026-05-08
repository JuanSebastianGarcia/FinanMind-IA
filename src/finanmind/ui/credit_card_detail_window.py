"""Per-card detail screen: cycle metrics, expenses, categories, payments, chart."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from tkinter import messagebox

import customtkinter as ctk

from finanmind.models.credit_card import CreditCard
from finanmind.models.credit_card_category import CreditCardCategory
from finanmind.models.credit_card_expense import CreditCardExpense
from finanmind.models.credit_card_payment import CreditCardPayment
from finanmind.services.credit_card_balance import CreditCardBalance
from finanmind.services.credit_card_billing_cycle import CreditCardBillingCycle
from finanmind.services.credit_card_service import CreditCardService
from finanmind.ui.budget_ui_theme import BudgetUiTheme
from finanmind.ui.credit_card_category_dialog import CreditCardCategoryDialog
from finanmind.ui.credit_card_dialog import CreditCardDialog
from finanmind.ui.credit_card_expense_dialog import CreditCardExpenseDialog
from finanmind.ui.credit_card_payment_dialog import CreditCardPaymentDialog
from finanmind.ui.currency_presenter import CurrencyPresenter
from finanmind.ui.percentage_presenter import PercentagePresenter


class CreditCardDetailWindow:
    """Owns layout and CRUD wiring for a single credit card view."""

    def __init__(
        self,
        host: ctk.CTkFrame,
        service: CreditCardService,
        card_id: str,
        on_back: Callable[[], None],
        on_card_deleted: Callable[[], None],
    ) -> None:
        self._host = host
        self._service = service
        self._card_id = card_id
        self._on_back = on_back
        self._on_card_deleted = on_card_deleted
        self._cycle_var = ctk.StringVar(value=self._default_cycle_key())
        self._title_lbl: ctk.CTkLabel | None = None
        self._summary_panel: ctk.CTkFrame | None = None
        self._expenses_panel: ctk.CTkScrollableFrame | None = None
        self._categories_panel: ctk.CTkScrollableFrame | None = None
        self._payments_panel: ctk.CTkScrollableFrame | None = None
        self._chart_panel: ctk.CTkFrame | None = None
        self._cycle_menu: ctk.CTkOptionMenu | None = None

    def attach(self) -> None:
        """Build widgets and render content."""
        outer = ctk.CTkFrame(self._host, fg_color=BudgetUiTheme.BG_MAIN)
        outer.pack(fill="both", expand=True, padx=20, pady=14)
        self._render_topbar(outer)
        self._render_summary_strip(outer)
        self._render_filter_strip(outer)
        self._render_split_region(outer)
        self.refresh()

    def refresh(self) -> None:
        """Re-render all dynamic regions from current state."""
        self._refresh_title()
        self._refresh_summary()
        self._refresh_cycle_menu()
        self._refresh_expenses_table()
        self._refresh_categories_panel()
        self._refresh_payments_panel()
        self._refresh_chart()

    def _default_cycle_key(self) -> str:
        today = date.today()
        return f"{today.year:04d}-{today.month:02d}"

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
        bar.pack(fill="x", pady=(0, 6))
        bar.pack_propagate(False)
        return bar

    def _populate_topbar(self, bar: ctk.CTkFrame) -> None:
        self._mount_topbar_back(bar)
        self._mount_topbar_title(bar)
        self._mount_topbar_actions(bar)

    def _mount_topbar_back(self, bar: ctk.CTkFrame) -> None:
        ctk.CTkButton(
            bar,
            text="← Tarjetas",
            command=self._on_back,
            fg_color="transparent",
            text_color=BudgetUiTheme.ACCENT,
            hover_color=BudgetUiTheme.INFO_BG,
            border_color=BudgetUiTheme.ACCENT,
            border_width=1,
            corner_radius=6,
            height=28,
            font=ctk.CTkFont(size=12),
            width=110,
        ).pack(side="left", padx=14, pady=14)

    def _mount_topbar_title(self, bar: ctk.CTkFrame) -> None:
        self._title_lbl = ctk.CTkLabel(
            bar,
            text="",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=BudgetUiTheme.TXT_PRI,
        )
        self._title_lbl.pack(side="left", padx=(8, 14), pady=14)

    def _mount_topbar_actions(self, bar: ctk.CTkFrame) -> None:
        self._mount_topbar_button(bar, "Eliminar tarjeta", self._handle_delete_card, danger=True)
        self._mount_topbar_button(bar, "Editar tarjeta", self._handle_edit_card, danger=False)
        self._mount_topbar_button(bar, "Registrar pago", self._handle_new_payment, danger=False)
        self._mount_topbar_button(bar, "Nuevo gasto", self._handle_new_expense, danger=False, primary=True)

    def _mount_topbar_button(
        self,
        bar: ctk.CTkFrame,
        text: str,
        cmd: Callable[[], None],
        *,
        danger: bool = False,
        primary: bool = False,
    ) -> None:
        button = self._build_topbar_button(bar, text, cmd, danger=danger, primary=primary)
        button.pack(side="right", padx=6, pady=12)

    def _build_topbar_button(
        self,
        bar: ctk.CTkFrame,
        text: str,
        cmd: Callable[[], None],
        *,
        danger: bool,
        primary: bool,
    ) -> ctk.CTkButton:
        if primary:
            return self._primary_button(bar, text, cmd)
        if danger:
            return self._danger_button(bar, text, cmd)
        return self._neutral_button(bar, text, cmd)

    def _primary_button(self, bar: ctk.CTkFrame, text: str, cmd: Callable[[], None]) -> ctk.CTkButton:
        return ctk.CTkButton(
            bar,
            text=text,
            command=cmd,
            fg_color=BudgetUiTheme.ACCENT,
            hover_color=BudgetUiTheme.ACCENT_HOVER,
            text_color="#ffffff",
            corner_radius=8,
            font=ctk.CTkFont(size=12),
            height=32,
            width=130,
        )

    def _danger_button(self, bar: ctk.CTkFrame, text: str, cmd: Callable[[], None]) -> ctk.CTkButton:
        return ctk.CTkButton(
            bar,
            text=text,
            command=cmd,
            fg_color="transparent",
            text_color=BudgetUiTheme.RED,
            hover_color=BudgetUiTheme.BADGE_WARN_BG,
            border_color=BudgetUiTheme.RED,
            border_width=1,
            corner_radius=8,
            font=ctk.CTkFont(size=12),
            height=32,
            width=140,
        )

    def _neutral_button(self, bar: ctk.CTkFrame, text: str, cmd: Callable[[], None]) -> ctk.CTkButton:
        return ctk.CTkButton(
            bar,
            text=text,
            command=cmd,
            fg_color="transparent",
            text_color=BudgetUiTheme.TXT_SEC,
            hover_color=BudgetUiTheme.BG_HOVER,
            border_color=BudgetUiTheme.BORDER,
            border_width=1,
            corner_radius=8,
            font=ctk.CTkFont(size=12),
            height=32,
            width=130,
        )

    def _render_summary_strip(self, outer: ctk.CTkFrame) -> None:
        wrap = ctk.CTkFrame(outer, fg_color="transparent")
        wrap.pack(fill="x", pady=(2, 6))
        for col in range(4):
            wrap.grid_columnconfigure(col, weight=1, uniform="summary")
        self._summary_panel = wrap

    def _refresh_title(self) -> None:
        if self._title_lbl is None:
            return
        try:
            card = self._service.card_by_id(self._card_id)
        except KeyError:
            self._title_lbl.configure(text="Tarjeta")
            return
        self._title_lbl.configure(text=card.name)

    def _refresh_summary(self) -> None:
        if self._summary_panel is None:
            return
        for child in self._summary_panel.winfo_children():
            child.destroy()
        try:
            card = self._service.card_by_id(self._card_id)
        except KeyError:
            return
        self._populate_summary(card)

    def _populate_summary(self, card: CreditCard) -> None:
        expenses = self._service.expenses_for_card(self._card_id)
        payments = self._service.payments_for_card(self._card_id)
        debt = CreditCardBalance.outstanding(expenses, payments)
        paid = CreditCardBalance.total_paid(payments)
        cycle_total = self._cycle_expenses_total()
        self._render_summary_card(0, "Deuda total", CurrencyPresenter.format_cop(debt), BudgetUiTheme.TXT_PRI)
        self._render_summary_card(1, "Total abonado", CurrencyPresenter.format_cop(paid), BudgetUiTheme.GREEN)
        self._render_summary_card(2, "Gasto del ciclo", CurrencyPresenter.format_cop(cycle_total), BudgetUiTheme.AMBER)
        self._render_summary_card(3, "Próxima cuota", f"Día {card.payment_due_day}", BudgetUiTheme.ACCENT)

    def _render_summary_card(self, col: int, caption: str, value: str, value_color: str) -> None:
        assert self._summary_panel is not None
        card = ctk.CTkFrame(
            self._summary_panel,
            fg_color=BudgetUiTheme.BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=BudgetUiTheme.BORDER,
        )
        card.grid(row=0, column=col, sticky="nsew", padx=4)
        self._populate_summary_card(card, caption, value, value_color)

    def _populate_summary_card(self, card: ctk.CTkFrame, caption: str, value: str, value_color: str) -> None:
        ctk.CTkLabel(
            card,
            text=caption,
            font=ctk.CTkFont(size=11),
            text_color=BudgetUiTheme.TXT_SEC,
        ).pack(anchor="w", padx=12, pady=(10, 0))
        ctk.CTkLabel(
            card,
            text=value,
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=value_color,
        ).pack(anchor="w", padx=12, pady=(2, 12))

    def _render_filter_strip(self, outer: ctk.CTkFrame) -> None:
        bar = ctk.CTkFrame(
            outer,
            fg_color=BudgetUiTheme.BG_CARD,
            corner_radius=10,
            border_width=1,
            border_color=BudgetUiTheme.BORDER,
        )
        bar.pack(fill="x", pady=(2, 6))
        self._populate_filter_strip(bar)

    def _populate_filter_strip(self, bar: ctk.CTkFrame) -> None:
        self._mount_filter_caption(bar)
        self._mount_filter_menu(bar)
        self._render_cycle_range_caption(bar)

    def _mount_filter_caption(self, bar: ctk.CTkFrame) -> None:
        ctk.CTkLabel(
            bar,
            text="Ciclo (corte en mes)",
            text_color=BudgetUiTheme.TXT_SEC,
            font=ctk.CTkFont(size=12),
        ).pack(side="left", padx=(14, 8), pady=10)

    def _mount_filter_menu(self, bar: ctk.CTkFrame) -> None:
        menu = ctk.CTkOptionMenu(
            bar,
            variable=self._cycle_var,
            values=[self._default_cycle_key()],
            command=self._handle_cycle_pick,
            fg_color=BudgetUiTheme.BG_MAIN,
            button_color=BudgetUiTheme.BORDER,
            button_hover_color=BudgetUiTheme.TXT_TER,
            dropdown_fg_color=BudgetUiTheme.BG_CARD,
            dropdown_text_color=BudgetUiTheme.TXT_PRI,
            text_color=BudgetUiTheme.TXT_PRI,
            height=30,
        )
        menu.pack(side="left", padx=4, pady=10)
        self._cycle_menu = menu

    def _render_cycle_range_caption(self, bar: ctk.CTkFrame) -> None:
        self._cycle_range_lbl = ctk.CTkLabel(
            bar,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=BudgetUiTheme.TXT_TER,
        )
        self._cycle_range_lbl.pack(side="left", padx=10)

    def _render_split_region(self, outer: ctk.CTkFrame) -> None:
        split = ctk.CTkFrame(outer, fg_color="transparent")
        split.pack(fill="both", expand=True)
        split.grid_columnconfigure(0, weight=2, minsize=620)
        split.grid_columnconfigure(1, weight=1, minsize=320)
        split.grid_rowconfigure(0, weight=1)
        self._mount_left_column(split)
        self._mount_right_column(split)

    def _mount_left_column(self, split: ctk.CTkFrame) -> None:
        left = ctk.CTkFrame(split, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self._render_expenses_panel(left)
        self._render_chart_panel(left)

    def _mount_right_column(self, split: ctk.CTkFrame) -> None:
        right = ctk.CTkFrame(split, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew")
        self._render_categories_panel(right)
        self._render_payments_panel(right)

    def _render_expenses_panel(self, left: ctk.CTkFrame) -> None:
        ctk.CTkLabel(
            left,
            text="Movimientos del ciclo",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=BudgetUiTheme.TXT_PRI,
        ).pack(anchor="w", pady=(2, 4))
        scroll = ctk.CTkScrollableFrame(
            left,
            fg_color=BudgetUiTheme.BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=BudgetUiTheme.BORDER,
            scrollbar_button_color=BudgetUiTheme.BORDER,
            scrollbar_button_hover_color=BudgetUiTheme.TXT_TER,
        )
        scroll.pack(fill="both", expand=True)
        self._expenses_panel = scroll

    def _render_chart_panel(self, left: ctk.CTkFrame) -> None:
        ctk.CTkLabel(
            left,
            text="Distribución por categoría",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=BudgetUiTheme.TXT_PRI,
        ).pack(anchor="w", pady=(10, 4))
        panel = ctk.CTkFrame(
            left,
            fg_color=BudgetUiTheme.BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=BudgetUiTheme.BORDER,
        )
        panel.pack(fill="x")
        self._chart_panel = panel

    def _render_categories_panel(self, right: ctk.CTkFrame) -> None:
        head = ctk.CTkFrame(right, fg_color="transparent")
        head.pack(fill="x", pady=(2, 4))
        self._mount_categories_header(head)
        scroll = self._build_side_scroll(right)
        scroll.pack(fill="both", expand=True, pady=(0, 10))
        self._categories_panel = scroll

    def _mount_categories_header(self, head: ctk.CTkFrame) -> None:
        self._mount_categories_title(head)
        self._mount_categories_add_btn(head)

    def _mount_categories_title(self, head: ctk.CTkFrame) -> None:
        ctk.CTkLabel(
            head,
            text="Categorías",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=BudgetUiTheme.TXT_PRI,
        ).pack(side="left")

    def _mount_categories_add_btn(self, head: ctk.CTkFrame) -> None:
        ctk.CTkButton(
            head,
            text="Agregar",
            command=self._handle_new_category,
            fg_color=BudgetUiTheme.BTN_ADD_LABEL_BG,
            text_color=BudgetUiTheme.BTN_ADD_LABEL_FG,
            hover_color=BudgetUiTheme.INFO_BG,
            corner_radius=6,
            height=26,
            width=88,
            font=ctk.CTkFont(size=11),
        ).pack(side="right")

    def _build_side_scroll(self, right: ctk.CTkFrame) -> ctk.CTkScrollableFrame:
        return ctk.CTkScrollableFrame(
            right,
            fg_color=BudgetUiTheme.BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=BudgetUiTheme.BORDER,
            scrollbar_button_color=BudgetUiTheme.BORDER,
            scrollbar_button_hover_color=BudgetUiTheme.TXT_TER,
        )

    def _render_payments_panel(self, right: ctk.CTkFrame) -> None:
        head = ctk.CTkFrame(right, fg_color="transparent")
        head.pack(fill="x", pady=(2, 4))
        ctk.CTkLabel(
            head,
            text="Pagos registrados",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=BudgetUiTheme.TXT_PRI,
        ).pack(side="left")
        scroll = self._build_side_scroll(right)
        scroll.pack(fill="both", expand=True)
        self._payments_panel = scroll

    def _refresh_cycle_menu(self) -> None:
        if self._cycle_menu is None:
            return
        merged = self._build_cycle_keys()
        self._cycle_menu.configure(values=merged)
        if self._cycle_var.get() not in merged:
            self._cycle_var.set(merged[0])
        self._refresh_cycle_caption()

    def _build_cycle_keys(self) -> list[str]:
        try:
            card = self._service.card_by_id(self._card_id)
        except KeyError:
            return [self._default_cycle_key()]
        anchor = date.today()
        rolling = CreditCardBillingCycle.cycle_keys_around(card.cut_day, anchor, span=6)
        observed = self._service.known_expense_months(self._card_id)
        merged = list(dict.fromkeys(rolling + observed))
        merged.sort(reverse=True)
        return merged or [self._default_cycle_key()]

    def _refresh_cycle_caption(self) -> None:
        try:
            start, end = self._current_cycle_range()
        except KeyError:
            return
        text = f"{start}  →  {end}"
        if hasattr(self, "_cycle_range_lbl") and self._cycle_range_lbl is not None:
            self._cycle_range_lbl.configure(text=text)

    def _current_cycle_range(self) -> tuple[str, str]:
        card = self._service.card_by_id(self._card_id)
        key = self._cycle_var.get().strip()
        year, month = self._parse_year_month(key)
        return CreditCardBillingCycle.cycle_for_month(card.cut_day, year, month)

    def _parse_year_month(self, key: str) -> tuple[int, int]:
        try:
            year_str, month_str = key.split("-")
            return int(year_str), int(month_str)
        except (ValueError, TypeError):
            today = date.today()
            return today.year, today.month

    def _handle_cycle_pick(self, _choice: str) -> None:
        self._refresh_cycle_caption()
        self._refresh_summary()
        self._refresh_expenses_table()
        self._refresh_chart()

    def _refresh_expenses_table(self) -> None:
        if self._expenses_panel is None:
            return
        for child in self._expenses_panel.winfo_children():
            child.destroy()
        rows = self._cycle_expenses()
        if not rows:
            self._render_empty_label(self._expenses_panel, "Sin movimientos en este ciclo.")
            return
        self._render_expenses_header()
        running = 0.0
        for ex in rows:
            running += ex.amount_cop
            self._render_expense_row(ex, running)

    def _render_empty_label(self, panel: ctk.CTkScrollableFrame, text: str) -> None:
        ctk.CTkLabel(
            panel,
            text=text,
            font=ctk.CTkFont(size=12),
            text_color=BudgetUiTheme.TXT_SEC,
        ).pack(anchor="w", padx=14, pady=12)

    def _render_expenses_header(self) -> None:
        assert self._expenses_panel is not None
        row = ctk.CTkFrame(self._expenses_panel, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=(8, 4))
        self._grid_cell(row, "Fecha", width=96, bold=True)
        self._grid_cell(row, "Descripción", width=200, bold=True)
        self._grid_cell(row, "Categoría", width=140, bold=True)
        self._grid_cell(row, "Valor", width=110, bold=True)
        self._grid_cell(row, "Acumulado", width=110, bold=True)
        self._grid_cell(row, "", width=80, bold=True)

    def _render_expense_row(self, ex: CreditCardExpense, running_total: float) -> None:
        assert self._expenses_panel is not None
        row = ctk.CTkFrame(self._expenses_panel, fg_color=BudgetUiTheme.BG_MAIN)
        row.pack(fill="x", padx=10, pady=2)
        category_caption = self._caption_for_category(ex.category_id)
        self._grid_cell(row, ex.occurred_on, width=96)
        self._grid_cell(row, ex.description or "—", width=200, wraplength=190)
        self._grid_cell(row, category_caption, width=140, wraplength=130)
        self._grid_cell(row, CurrencyPresenter.format_cop(ex.amount_cop), width=110)
        self._grid_cell(row, CurrencyPresenter.format_cop(running_total), width=110)
        self._render_expense_actions(row, ex)

    def _render_expense_actions(self, row: ctk.CTkFrame, ex: CreditCardExpense) -> None:
        self._mount_expense_edit_btn(row, ex.expense_id)
        self._mount_expense_delete_btn(row, ex.expense_id)

    def _mount_expense_edit_btn(self, row: ctk.CTkFrame, expense_id: str) -> None:
        ctk.CTkButton(
            row,
            text="Editar",
            width=72,
            height=24,
            command=lambda eid=expense_id: self._handle_edit_expense(eid),
            fg_color="transparent",
            text_color=BudgetUiTheme.TXT_SEC,
            hover_color=BudgetUiTheme.BG_HOVER,
            border_color=BudgetUiTheme.BORDER,
            border_width=1,
            corner_radius=6,
            font=ctk.CTkFont(size=11),
        ).pack(side="left", padx=4, pady=4)

    def _mount_expense_delete_btn(self, row: ctk.CTkFrame, expense_id: str) -> None:
        ctk.CTkButton(
            row,
            text="Quitar",
            width=72,
            height=24,
            command=lambda eid=expense_id: self._handle_delete_expense(eid),
            fg_color="transparent",
            text_color=BudgetUiTheme.RED,
            hover_color=BudgetUiTheme.BADGE_WARN_BG,
            border_color=BudgetUiTheme.RED,
            border_width=1,
            corner_radius=6,
            font=ctk.CTkFont(size=11),
        ).pack(side="left", padx=4, pady=4)

    def _grid_cell(
        self,
        row: ctk.CTkFrame,
        text: str,
        width: int,
        bold: bool = False,
        wraplength: int | None = None,
    ) -> None:
        font = ctk.CTkFont(weight="bold") if bold else ctk.CTkFont()
        kwargs = self._cell_kwargs(text, width, font, wraplength)
        ctk.CTkLabel(row, **kwargs).pack(side="left", padx=4, pady=2)

    def _cell_kwargs(self, text: str, width: int, font: ctk.CTkFont, wraplength: int | None) -> dict:
        if wraplength is None:
            return dict(text=text, width=width, anchor="w", font=font, text_color=BudgetUiTheme.TXT_PRI)
        return dict(
            text=text,
            width=width,
            anchor="nw",
            justify="left",
            wraplength=wraplength,
            font=font,
            text_color=BudgetUiTheme.TXT_PRI,
        )

    def _refresh_categories_panel(self) -> None:
        if self._categories_panel is None:
            return
        for child in self._categories_panel.winfo_children():
            child.destroy()
        cats = self._service.categories_for_card(self._card_id)
        if not cats:
            self._render_empty_label(self._categories_panel, "Sin categorías. Crea la primera para clasificar tus gastos.")
            return
        for cat in cats:
            self._render_category_row(cat)

    def _render_category_row(self, cat: CreditCardCategory) -> None:
        assert self._categories_panel is not None
        row = ctk.CTkFrame(self._categories_panel, fg_color=BudgetUiTheme.BG_MAIN, corner_radius=8)
        row.pack(fill="x", padx=8, pady=4)
        self._mount_category_swatch(row, cat.color)
        self._mount_category_title(row, cat.title)
        self._mount_category_actions(row, cat.category_id)

    def _mount_category_swatch(self, row: ctk.CTkFrame, color: str) -> None:
        swatch = ctk.CTkFrame(row, fg_color=color or BudgetUiTheme.BORDER, corner_radius=4, width=12, height=22)
        swatch.pack(side="left", padx=(8, 6), pady=8)
        swatch.pack_propagate(False)

    def _mount_category_title(self, row: ctk.CTkFrame, title: str) -> None:
        ctk.CTkLabel(
            row,
            text=title,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=BudgetUiTheme.TXT_PRI,
            anchor="w",
        ).pack(side="left", fill="x", expand=True)

    def _mount_category_actions(self, row: ctk.CTkFrame, category_id: str) -> None:
        self._mount_category_edit_btn(row, category_id)
        self._mount_category_delete_btn(row, category_id)

    def _mount_category_edit_btn(self, row: ctk.CTkFrame, category_id: str) -> None:
        ctk.CTkButton(
            row,
            text="Editar",
            width=58,
            height=22,
            command=lambda cid=category_id: self._handle_edit_category(cid),
            fg_color="transparent",
            text_color=BudgetUiTheme.TXT_SEC,
            hover_color=BudgetUiTheme.BG_HOVER,
            border_color=BudgetUiTheme.BORDER,
            border_width=1,
            corner_radius=6,
            font=ctk.CTkFont(size=10),
        ).pack(side="left", padx=2, pady=4)

    def _mount_category_delete_btn(self, row: ctk.CTkFrame, category_id: str) -> None:
        ctk.CTkButton(
            row,
            text="✕",
            width=28,
            height=22,
            command=lambda cid=category_id: self._handle_delete_category(cid),
            fg_color="transparent",
            text_color=BudgetUiTheme.RED,
            hover_color=BudgetUiTheme.BADGE_WARN_BG,
            border_color=BudgetUiTheme.RED,
            border_width=1,
            corner_radius=6,
            font=ctk.CTkFont(size=10),
        ).pack(side="left", padx=(2, 8), pady=4)

    def _refresh_payments_panel(self) -> None:
        if self._payments_panel is None:
            return
        for child in self._payments_panel.winfo_children():
            child.destroy()
        pays = self._service.payments_for_card(self._card_id)
        if not pays:
            self._render_empty_label(self._payments_panel, "Sin pagos registrados.")
            return
        for pay in sorted(pays, key=lambda p: p.paid_on, reverse=True):
            self._render_payment_row(pay)

    def _render_payment_row(self, pay: CreditCardPayment) -> None:
        assert self._payments_panel is not None
        row = ctk.CTkFrame(self._payments_panel, fg_color=BudgetUiTheme.BG_MAIN, corner_radius=8)
        row.pack(fill="x", padx=8, pady=4)
        body = ctk.CTkFrame(row, fg_color="transparent")
        body.pack(fill="x", padx=8, pady=6)
        self._mount_payment_top_row(body, pay)
        if pay.notes.strip():
            ctk.CTkLabel(
                body,
                text=pay.notes.strip(),
                font=ctk.CTkFont(size=11),
                text_color=BudgetUiTheme.TXT_TER,
                anchor="w",
            ).pack(fill="x")

    def _mount_payment_top_row(self, body: ctk.CTkFrame, pay: CreditCardPayment) -> None:
        top = ctk.CTkFrame(body, fg_color="transparent")
        top.pack(fill="x")
        ctk.CTkLabel(
            top,
            text=pay.paid_on,
            font=ctk.CTkFont(size=12),
            text_color=BudgetUiTheme.TXT_SEC,
        ).pack(side="left")
        ctk.CTkLabel(
            top,
            text=CurrencyPresenter.format_cop(pay.amount_cop),
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=BudgetUiTheme.GREEN,
        ).pack(side="left", padx=(10, 6))
        self._mount_payment_delete(top, pay.payment_id)

    def _mount_payment_delete(self, top: ctk.CTkFrame, payment_id: str) -> None:
        ctk.CTkButton(
            top,
            text="Quitar",
            width=64,
            height=22,
            command=lambda pid=payment_id: self._handle_delete_payment(pid),
            fg_color="transparent",
            text_color=BudgetUiTheme.RED,
            hover_color=BudgetUiTheme.BADGE_WARN_BG,
            border_color=BudgetUiTheme.RED,
            border_width=1,
            corner_radius=6,
            font=ctk.CTkFont(size=10),
        ).pack(side="right")

    def _refresh_chart(self) -> None:
        if self._chart_panel is None:
            return
        for child in self._chart_panel.winfo_children():
            child.destroy()
        rows = self._cycle_expenses()
        totals = CreditCardBalance.per_category_totals(rows)
        if not rows:
            self._render_chart_empty()
            return
        self._render_chart_bars(totals, sum(totals.values()))

    def _render_chart_empty(self) -> None:
        assert self._chart_panel is not None
        ctk.CTkLabel(
            self._chart_panel,
            text="Sin gastos en el ciclo seleccionado.",
            font=ctk.CTkFont(size=12),
            text_color=BudgetUiTheme.TXT_SEC,
        ).pack(padx=14, pady=14)

    def _render_chart_bars(self, totals: dict[str, float], grand_total: float) -> None:
        ordered = sorted(totals.items(), key=lambda item: item[1], reverse=True)
        for category_id, value in ordered:
            self._render_chart_bar(category_id, value, grand_total)

    def _render_chart_bar(self, category_id: str, value: float, grand_total: float) -> None:
        assert self._chart_panel is not None
        row = ctk.CTkFrame(self._chart_panel, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=6)
        self._mount_chart_caption(row, category_id, value, grand_total)
        ratio = (value / grand_total) if grand_total > 0 else 0.0
        bar = ctk.CTkProgressBar(row, height=8, progress_color=self._color_for_category(category_id))
        bar.set(min(max(ratio, 0.0), 1.0))
        bar.pack(fill="x", pady=(4, 0))

    def _mount_chart_caption(
        self,
        row: ctk.CTkFrame,
        category_id: str,
        value: float,
        grand_total: float,
    ) -> None:
        head = ctk.CTkFrame(row, fg_color="transparent")
        head.pack(fill="x")
        ctk.CTkLabel(
            head,
            text=self._caption_for_category(category_id),
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=BudgetUiTheme.TXT_PRI,
        ).pack(side="left")
        pct = (value / grand_total * 100) if grand_total > 0 else 0
        ctk.CTkLabel(
            head,
            text=f"{CurrencyPresenter.format_cop(value)} · {PercentagePresenter.format_pct(pct)}",
            font=ctk.CTkFont(size=11),
            text_color=BudgetUiTheme.TXT_SEC,
        ).pack(side="right")

    def _caption_for_category(self, category_id: str) -> str:
        if category_id == "":
            return "Sin categoría"
        try:
            cat = self._service.category_by_id(category_id)
        except KeyError:
            return "Sin categoría"
        return cat.title

    def _color_for_category(self, category_id: str) -> str:
        try:
            cat = self._service.category_by_id(category_id)
        except KeyError:
            return BudgetUiTheme.ACCENT
        return cat.color or BudgetUiTheme.ACCENT

    def _cycle_expenses(self) -> list[CreditCardExpense]:
        try:
            start, end = self._current_cycle_range()
        except KeyError:
            return []
        return self._service.expenses_in_range(self._card_id, start, end)

    def _cycle_expenses_total(self) -> float:
        return sum(e.amount_cop for e in self._cycle_expenses())

    def _handle_edit_card(self) -> None:
        try:
            card = self._service.card_by_id(self._card_id)
        except KeyError:
            return
        payload = self._show_card_dialog(card)
        if payload is None:
            return
        try:
            self._service.update_card(self._card_id, *payload)
        except ValueError as exc:
            messagebox.showwarning("Tarjeta", str(exc))
            return
        self.refresh()

    def _show_card_dialog(self, card: CreditCard) -> tuple[str, float, int, int, str] | None:
        dialog = CreditCardDialog(
            self._host.winfo_toplevel(),
            "Editar tarjeta",
            seed_name=card.name,
            seed_limit=card.limit_cop,
            seed_cut_day=card.cut_day,
            seed_due_day=card.payment_due_day,
            seed_color=card.color,
        )
        return dialog.show()

    def _handle_delete_card(self) -> None:
        if not messagebox.askyesno("Eliminar tarjeta", "¿Eliminar esta tarjeta y todos sus gastos y pagos?"):
            return
        try:
            self._service.delete_card(self._card_id)
        except KeyError:
            messagebox.showwarning("Tarjeta", "No se encontró la tarjeta.")
            return
        self._on_card_deleted()

    def _handle_new_category(self) -> None:
        dialog = CreditCardCategoryDialog(
            self._host.winfo_toplevel(),
            "Nueva categoría",
            seed_title="",
            seed_color="",
        )
        payload = dialog.show()
        if payload is None:
            return
        try:
            self._service.add_category(self._card_id, *payload)
        except ValueError as exc:
            messagebox.showwarning("Categoría", str(exc))
            return
        self.refresh()

    def _handle_edit_category(self, category_id: str) -> None:
        try:
            cat = self._service.category_by_id(category_id)
        except KeyError:
            return
        dialog = CreditCardCategoryDialog(
            self._host.winfo_toplevel(),
            "Editar categoría",
            seed_title=cat.title,
            seed_color=cat.color,
        )
        payload = dialog.show()
        if payload is None:
            return
        self._save_category_update(category_id, payload)

    def _save_category_update(self, category_id: str, payload: tuple[str, str]) -> None:
        try:
            self._service.update_category(category_id, *payload)
        except ValueError as exc:
            messagebox.showwarning("Categoría", str(exc))
            return
        self.refresh()

    def _handle_delete_category(self, category_id: str) -> None:
        if not messagebox.askyesno("Categoría", "¿Eliminar esta categoría? Los gastos quedarán sin categoría."):
            return
        try:
            self._service.delete_category(category_id)
        except KeyError:
            messagebox.showwarning("Categoría", "No se encontró la categoría.")
            return
        self.refresh()

    def _handle_new_expense(self) -> None:
        cats = self._service.categories_for_card(self._card_id)
        payload = self._show_new_expense_dialog(cats)
        if payload is None:
            return
        self._save_new_expense(payload)

    def _show_new_expense_dialog(
        self,
        cats: list[CreditCardCategory],
    ) -> tuple[float, str, str, str, int, str] | None:
        dialog = CreditCardExpenseDialog(
            self._host.winfo_toplevel(),
            "Nuevo gasto",
            categories=cats,
            seed_amount=0.0,
            seed_description="",
            seed_category_id="",
            seed_day="",
            seed_installments=1,
            seed_notes="",
        )
        return dialog.show()

    def _save_new_expense(self, payload: tuple[float, str, str, str, int, str]) -> None:
        amount, desc, cat_id, day, inst, notes = payload
        try:
            self._service.add_expense(self._card_id, cat_id, day, amount, desc, inst, notes)
        except ValueError as exc:
            messagebox.showwarning("Gasto", str(exc))
            return
        self.refresh()

    def _handle_edit_expense(self, expense_id: str) -> None:
        try:
            ex = self._service.expense_by_id(expense_id)
        except KeyError:
            return
        cats = self._service.categories_for_card(self._card_id)
        payload = self._show_expense_dialog(ex, cats)
        if payload is None:
            return
        self._save_expense_update(expense_id, payload)

    def _show_expense_dialog(
        self,
        ex: CreditCardExpense,
        cats: list[CreditCardCategory],
    ) -> tuple[float, str, str, str, int, str] | None:
        dialog = CreditCardExpenseDialog(
            self._host.winfo_toplevel(),
            "Editar gasto",
            categories=cats,
            seed_amount=ex.amount_cop,
            seed_description=ex.description,
            seed_category_id=ex.category_id,
            seed_day=ex.occurred_on,
            seed_installments=ex.installments,
            seed_notes=ex.notes,
        )
        return dialog.show()

    def _save_expense_update(
        self,
        expense_id: str,
        payload: tuple[float, str, str, str, int, str],
    ) -> None:
        amount, desc, cat_id, day, inst, notes = payload
        try:
            self._service.update_expense(expense_id, cat_id, day, amount, desc, inst, notes)
        except ValueError as exc:
            messagebox.showwarning("Gasto", str(exc))
            return
        self.refresh()

    def _handle_delete_expense(self, expense_id: str) -> None:
        if not messagebox.askyesno("Gasto", "¿Eliminar este gasto?"):
            return
        try:
            self._service.delete_expense(expense_id)
        except KeyError:
            messagebox.showwarning("Gasto", "No se encontró el gasto.")
            return
        self.refresh()

    def _handle_new_payment(self) -> None:
        dialog = CreditCardPaymentDialog(self._host.winfo_toplevel())
        payload = dialog.show()
        if payload is None:
            return
        day, amount, notes = payload
        try:
            self._service.add_payment(self._card_id, day, amount, notes)
        except ValueError as exc:
            messagebox.showwarning("Pago", str(exc))
            return
        self.refresh()

    def _handle_delete_payment(self, payment_id: str) -> None:
        if not messagebox.askyesno("Pago", "¿Eliminar este pago?"):
            return
        try:
            self._service.delete_payment(payment_id)
        except KeyError:
            messagebox.showwarning("Pago", "No se encontró el pago.")
            return
        self.refresh()
