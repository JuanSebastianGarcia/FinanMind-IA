"""Monthly distribution ledger versus fixed budget labels."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from tkinter import messagebox

import customtkinter as ctk

from finanmind.models.budget_workspace import BudgetWorkspace
from finanmind.models.income_distribution_line import IncomeDistributionLine
from finanmind.models.income_receipt import IncomeReceipt
from finanmind.budget.book_service import BudgetBookService
from finanmind.services.monthly_distribution_service import MonthlyDistributionService
from finanmind.ui.currency_presenter import CurrencyPresenter
from finanmind.ui.distribution_line_dialog import DistributionLineDialog
from finanmind.ui.distribution_receipt_dialog import DistributionReceiptDialog
from finanmind.ui.budget_ui_theme import BudgetUiTheme


class MonthlyDistributionWindow:
    """Registers payroll receipts, allocations, and compares spend to budget."""

    def __init__(
        self,
        host: ctk.CTkFrame,
        budget_book: BudgetBookService,
        ledger: MonthlyDistributionService,
    ) -> None:
        self._host = host
        self._book = budget_book
        self._ledger = ledger
        self._month_var = ctk.StringVar(value="")
        self._receipt_var = ctk.StringVar(value="")
        self._remainder_lbl: ctk.CTkLabel | None = None
        self._ledger_panel: ctk.CTkScrollableFrame | None = None
        self._summary_panel: ctk.CTkScrollableFrame | None = None
        self._month_menu: ctk.CTkOptionMenu | None = None
        self._month_keys: list[str] = []
        self._receipt_menu: ctk.CTkOptionMenu | None = None
        self._caption_to_receipt: dict[str, str] = {}

    def attach(self) -> None:
        """Build widgets and seed selectors from current in-memory data."""
        outer = ctk.CTkFrame(self._host, fg_color=BudgetUiTheme.BG_MAIN)
        outer.pack(fill="both", expand=True, padx=20, pady=14)
        self._render_topbar(outer)
        self._render_hint(outer)
        self._render_filter_strip(outer)
        self._render_split_region(outer)
        self._bootstrap_months()

    def refresh(self) -> None:
        """Re-render menus and rows from current state without losing selection."""
        self._reload_month_menu(select_latest=False)
        self._reload_receipt_menu(select_first=False)
        self._refresh_views()

    def _dialog_parent(self) -> ctk.Misc:
        return self._host.winfo_toplevel()

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
        self._mount_topbar_actions(bar)

    def _mount_topbar_title(self, bar: ctk.CTkFrame) -> None:
        title = ctk.CTkLabel(
            bar,
            text="Distribución mensual",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=BudgetUiTheme.TXT_PRI,
        )
        title.pack(side="left", padx=20, pady=14)

    def _mount_topbar_actions(self, bar: ctk.CTkFrame) -> None:
        self._mount_topbar_button(bar, "Nuevo ingreso", self._handle_new_receipt, primary=True)
        self._mount_topbar_button(bar, "Eliminar ingreso", self._handle_delete_receipt, danger=True)

    def _mount_topbar_button(
        self,
        bar: ctk.CTkFrame,
        text: str,
        cmd: Callable[[], None],
        *,
        primary: bool = False,
        danger: bool = False,
    ) -> None:
        button = self._build_topbar_button(bar, text, cmd, primary=primary, danger=danger)
        button.pack(side="right", padx=6, pady=12)

    def _build_topbar_button(
        self,
        bar: ctk.CTkFrame,
        text: str,
        cmd: Callable[[], None],
        *,
        primary: bool,
        danger: bool,
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
            width=140,
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
            width=140,
        )

    def _render_hint(self, outer: ctk.CTkFrame) -> None:
        hint = ctk.CTkLabel(
            outer,
            text="Registra ingresos y cómo se reparten en las etiquetas del presupuesto.",
            font=ctk.CTkFont(size=12),
            text_color=BudgetUiTheme.TXT_SEC,
        )
        hint.pack(anchor="w", pady=(8, 6))

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
        self._mount_filter_caption(bar, "Mes")
        self._mount_month_menu(bar)
        self._mount_filter_caption(bar, "Ingreso")
        self._mount_receipt_menu(bar)
        self._mount_remainder_label(bar)
        self._mount_register_button(bar)

    def _mount_filter_caption(self, bar: ctk.CTkFrame, caption: str) -> None:
        ctk.CTkLabel(
            bar,
            text=caption,
            text_color=BudgetUiTheme.TXT_SEC,
            font=ctk.CTkFont(size=12),
        ).pack(side="left", padx=(14, 6), pady=10)

    def _mount_month_menu(self, bar: ctk.CTkFrame) -> None:
        menu = ctk.CTkOptionMenu(
            bar,
            variable=self._month_var,
            values=["—"],
            command=self._handle_month_pick,
            **self._option_menu_kwargs(),
        )
        menu.pack(side="left", padx=(0, 6), pady=10)
        self._month_menu = menu

    def _mount_receipt_menu(self, bar: ctk.CTkFrame) -> None:
        menu = ctk.CTkOptionMenu(
            bar,
            variable=self._receipt_var,
            values=["—"],
            command=self._handle_receipt_pick,
            **self._option_menu_kwargs(),
        )
        menu.pack(side="left", padx=(0, 12), pady=10)
        self._receipt_menu = menu

    def _mount_remainder_label(self, bar: ctk.CTkFrame) -> None:
        self._remainder_lbl = ctk.CTkLabel(
            bar,
            text="",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=BudgetUiTheme.TXT_SEC,
        )
        self._remainder_lbl.pack(side="left", padx=(0, 8), pady=10)

    def _mount_register_button(self, bar: ctk.CTkFrame) -> None:
        ctk.CTkButton(
            bar,
            text="Registrar distribución",
            command=self._handle_new_line,
            fg_color=BudgetUiTheme.ACCENT,
            hover_color=BudgetUiTheme.ACCENT_HOVER,
            text_color="#ffffff",
            corner_radius=8,
            font=ctk.CTkFont(size=12),
            height=30,
            width=170,
        ).pack(side="right", padx=14, pady=10)

    def _option_menu_kwargs(self) -> dict:
        return {
            "fg_color": BudgetUiTheme.BG_MAIN,
            "button_color": BudgetUiTheme.BORDER,
            "button_hover_color": BudgetUiTheme.TXT_TER,
            "dropdown_fg_color": BudgetUiTheme.BG_CARD,
            "dropdown_text_color": BudgetUiTheme.TXT_PRI,
            "text_color": BudgetUiTheme.TXT_PRI,
            "height": 30,
        }

    def _render_split_region(self, outer: ctk.CTkFrame) -> None:
        split = ctk.CTkFrame(outer, fg_color="transparent")
        split.pack(fill="both", expand=True, pady=(2, 0))
        split.grid_columnconfigure(0, weight=2, minsize=600)
        split.grid_columnconfigure(1, weight=1, minsize=540)
        split.grid_rowconfigure(0, weight=1)
        self._mount_left_column(split)
        self._mount_right_column(split)

    def _mount_left_column(self, split: ctk.CTkFrame) -> None:
        left = ctk.CTkFrame(split, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self._render_ledger_section(left)

    def _mount_right_column(self, split: ctk.CTkFrame) -> None:
        right = ctk.CTkFrame(split, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew")
        self._render_summary_section(right)

    def _render_ledger_section(self, left: ctk.CTkFrame) -> None:
        ctk.CTkLabel(
            left,
            text="Movimientos del ingreso",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=BudgetUiTheme.TXT_PRI,
        ).pack(anchor="w", pady=(2, 4))
        self._ledger_panel = self._build_card_scroll(left)
        self._ledger_panel.pack(fill="both", expand=True)

    def _render_summary_section(self, right: ctk.CTkFrame) -> None:
        ctk.CTkLabel(
            right,
            text="Resumen del mes vs presupuesto",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=BudgetUiTheme.TXT_PRI,
        ).pack(anchor="w", pady=(2, 4))
        self._summary_panel = self._build_card_scroll(right)
        self._summary_panel.pack(fill="both", expand=True)

    def _build_card_scroll(self, parent: ctk.CTkFrame) -> ctk.CTkScrollableFrame:
        return ctk.CTkScrollableFrame(
            parent,
            fg_color=BudgetUiTheme.BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=BudgetUiTheme.BORDER,
            scrollbar_button_color=BudgetUiTheme.BORDER,
            scrollbar_button_hover_color=BudgetUiTheme.TXT_TER,
        )

    def _bootstrap_months(self) -> None:
        self._reload_month_menu(select_latest=True)
        self._reload_receipt_menu(select_first=True)
        self._refresh_views()

    def _reload_month_menu(self, select_latest: bool) -> None:
        assert self._month_menu is not None
        tokens = self._ledger.known_month_prefixes()
        current = date.today().strftime("%Y-%m")
        merged = self._merge_month_tokens(tokens, current)
        if not merged:
            merged = [current]
        self._month_keys = merged
        self._month_menu.configure(values=merged)
        chosen = merged[0] if select_latest else self._coerce_existing_month(merged)
        self._month_var.set(chosen)

    def _merge_month_tokens(self, tokens: list[str], current: str) -> list[str]:
        ordered = list(dict.fromkeys(tokens))
        if current not in ordered:
            ordered.insert(0, current)
        return ordered

    def _coerce_existing_month(self, merged: list[str]) -> str:
        current = self._month_var.get().strip()
        return current if current in merged else merged[0]

    def _handle_month_pick(self, choice: str) -> None:
        self._month_var.set(choice)
        self._reload_receipt_menu(select_first=True)
        self._refresh_views()

    def _reload_receipt_menu(self, select_first: bool) -> None:
        assert self._receipt_menu is not None
        month_key = self._month_var.get().strip()
        receipts = self._ledger.receipts_in_month(month_key)
        if not receipts:
            self._caption_to_receipt = {}
            self._receipt_menu.configure(values=["Sin ingresos este mes"])
            self._receipt_var.set("Sin ingresos este mes")
            return
        self._publish_receipt_options(receipts, select_first)

    def _publish_receipt_options(
        self,
        receipts: list[IncomeReceipt],
        select_first: bool,
    ) -> None:
        assert self._receipt_menu is not None
        captions = [self._receipt_caption(rec) for rec in receipts]
        self._caption_to_receipt = {captions[i]: receipts[i].receipt_id for i in range(len(captions))}
        self._receipt_menu.configure(values=captions)
        target = captions[0] if select_first else self._safe_receipt_caption(captions)
        self._receipt_var.set(target)

    def _safe_receipt_caption(self, captions: list[str]) -> str:
        current = self._receipt_var.get()
        return current if current in captions else captions[0]

    def _handle_receipt_pick(self, choice: str) -> None:
        self._receipt_var.set(choice)
        self._refresh_views()

    def _refresh_views(self) -> None:
        self._render_remainder()
        self._render_ledger_rows()
        self._render_summary_rows()

    def _render_remainder(self) -> None:
        assert self._remainder_lbl is not None
        receipt_id = self._active_receipt_id()
        if receipt_id is None:
            self._remainder_lbl.configure(text="Selecciona un ingreso", text_color=BudgetUiTheme.TXT_SEC)
            return
        remainder = self._ledger.remaining_for_receipt(receipt_id)
        label = f"Por distribuir: {CurrencyPresenter.format_cop(remainder)}"
        tone = BudgetUiTheme.RED if remainder < 0 else BudgetUiTheme.TXT_PRI
        self._remainder_lbl.configure(text=label, text_color=tone)

    def _active_receipt_id(self) -> str | None:
        caption = self._receipt_var.get().strip()
        return self._caption_to_receipt.get(caption)

    def _render_ledger_rows(self) -> None:
        assert self._ledger_panel is not None
        for child in self._ledger_panel.winfo_children():
            child.destroy()
        receipt_id = self._active_receipt_id()
        if receipt_id is None:
            self._render_empty_ledger("No hay ingreso seleccionado.")
            return
        receipt = self._ledger.receipt_by_id(receipt_id)
        lines = self._ledger.lines_for_receipt(receipt_id)
        self._append_ledger_header()
        self._append_income_row(receipt, receipt.amount_cop)
        self._append_line_rows(receipt_id, lines, receipt.amount_cop)

    def _append_line_rows(
        self,
        receipt_id: str,
        lines: list[IncomeDistributionLine],
        opening_balance: float,
    ) -> None:
        balance = opening_balance
        for ln in lines:
            balance -= ln.amount_cop
            self._append_line_row(receipt_id, ln, balance)

    def _render_empty_ledger(self, msg: str) -> None:
        assert self._ledger_panel is not None
        ctk.CTkLabel(
            self._ledger_panel,
            text=msg,
            text_color=BudgetUiTheme.TXT_SEC,
        ).pack(anchor="w", padx=12, pady=12)

    def _append_ledger_header(self) -> None:
        assert self._ledger_panel is not None
        row = ctk.CTkFrame(self._ledger_panel, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=(8, 4))
        self._mount_action_spacer(row, width=82)
        self._grid_cell(row, "Fecha", bold=True, width=96)
        self._grid_cell(row, "Concepto", bold=True, width=150)
        self._grid_cell(row, "Monto", bold=True, width=118)
        self._grid_cell(row, "Saldo ingreso", bold=True, width=150)

    def _append_income_row(self, receipt: IncomeReceipt, balance: float) -> None:
        assert self._ledger_panel is not None
        row = ctk.CTkFrame(self._ledger_panel, fg_color=BudgetUiTheme.BG_MAIN, corner_radius=8)
        row.pack(fill="x", padx=10, pady=3)
        self._mount_action_spacer(row, width=82)
        concept = self._income_concept(receipt)
        self._grid_cell(row, receipt.occurred_on, width=96)
        self._grid_cell(row, concept, width=150, wraplength=138)
        self._grid_cell(row, CurrencyPresenter.format_cop(receipt.amount_cop), width=118)
        self._grid_cell(row, CurrencyPresenter.format_cop(balance), width=150)

    def _income_concept(self, receipt: IncomeReceipt) -> str:
        memo = receipt.memo.strip()
        return f"Ingreso · {memo}" if memo else "Ingreso registrado"

    def _append_line_row(
        self,
        receipt_id: str,
        ln: IncomeDistributionLine,
        balance: float,
    ) -> None:
        assert self._ledger_panel is not None
        row = ctk.CTkFrame(self._ledger_panel, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=2)
        self._mount_quit_line_button(row, ln)
        workspace = self._book.peek()
        title = self._resolve_label_title(workspace, ln.label_id)
        concept = title if ln.memo.strip() == "" else f"{title} · {ln.memo.strip()}"
        self._grid_cell(row, ln.occurred_on, width=96)
        self._grid_cell(row, concept, width=150, wraplength=138)
        self._grid_cell(row, CurrencyPresenter.format_cop(ln.amount_cop), width=118)
        self._mount_balance_cell(row, balance)

    def _mount_action_spacer(self, row: ctk.CTkFrame, width: int) -> None:
        spacer = ctk.CTkFrame(row, fg_color="transparent", width=width, height=1)
        spacer.pack(side="right", padx=6)
        spacer.pack_propagate(False)

    def _mount_balance_cell(self, row: ctk.CTkFrame, balance: float) -> None:
        tone = BudgetUiTheme.RED if balance < 0 else BudgetUiTheme.TXT_PRI
        ctk.CTkLabel(
            row,
            text=CurrencyPresenter.format_cop(balance),
            width=150,
            anchor="w",
            text_color=tone,
        ).pack(side="left", padx=6)

    def _mount_quit_line_button(self, row: ctk.CTkFrame, ln: IncomeDistributionLine) -> None:
        ctk.CTkButton(
            row,
            text="Quitar",
            width=82,
            height=24,
            fg_color="transparent",
            border_width=1,
            border_color=BudgetUiTheme.BORDER,
            text_color=BudgetUiTheme.TXT_SEC,
            hover_color=BudgetUiTheme.BG_HOVER,
            corner_radius=6,
            font=ctk.CTkFont(size=11),
            command=lambda: self._confirm_delete_line(ln.line_id),
        ).pack(side="right", padx=6)

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
        ctk.CTkLabel(row, **kwargs).pack(side="left", padx=6, pady=2)

    def _cell_kwargs(
        self,
        text: str,
        width: int,
        font: ctk.CTkFont,
        wraplength: int | None,
    ) -> dict:
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

    def _render_summary_rows(self) -> None:
        assert self._summary_panel is not None
        for child in self._summary_panel.winfo_children():
            child.destroy()
        rows = self._build_summary_rows()
        self._mount_summary_header()
        if not rows:
            self._render_summary_empty()
            return
        for entry in rows:
            self._append_summary_row(*entry)

    def _build_summary_rows(self) -> list[tuple[str, str, float, float, float, str]]:
        workspace = self._book.peek()
        month_key = self._month_var.get().strip()
        spent_map = self._ledger.monthly_spent_by_label(month_key)
        rows: list[tuple[str, str, float, float, float, str]] = []
        for title, label_id, budget_amt, color in self._flatten_budget_labels(workspace):
            spent = spent_map.get(label_id, 0.0)
            diff = budget_amt - spent
            rows.append((title, label_id, budget_amt, spent, diff, color))
        return rows

    def _render_summary_empty(self) -> None:
        assert self._summary_panel is not None
        ctk.CTkLabel(
            self._summary_panel,
            text="Sin etiquetas en el presupuesto.",
            text_color=BudgetUiTheme.TXT_SEC,
        ).pack(anchor="w", padx=12, pady=10)

    def _mount_summary_header(self) -> None:
        assert self._summary_panel is not None
        header = ctk.CTkFrame(self._summary_panel, fg_color="transparent")
        header.pack(fill="x", padx=8, pady=(8, 4))
        bold = ctk.CTkFont(size=12, weight="bold")
        self._mount_summary_header_money(header, bold)
        self._mount_summary_header_title(header, bold)

    def _mount_summary_header_money(self, header: ctk.CTkFrame, bold: ctk.CTkFont) -> None:
        w = 96
        ctk.CTkLabel(header, text="Diff.", font=bold, width=w, anchor="e",
                     text_color=BudgetUiTheme.TXT_PRI).pack(side="right", padx=(4, 4))
        ctk.CTkLabel(header, text="Dist.", font=bold, width=w, anchor="e",
                     text_color=BudgetUiTheme.TXT_PRI).pack(side="right", padx=(0, 4))
        ctk.CTkLabel(header, text="Ppto.", font=bold, width=w, anchor="e",
                     text_color=BudgetUiTheme.TXT_PRI).pack(side="right", padx=(0, 4))

    def _mount_summary_header_title(self, header: ctk.CTkFrame, bold: ctk.CTkFont) -> None:
        spacer = ctk.CTkFrame(header, fg_color="transparent", width=18, height=1)
        spacer.pack(side="left", padx=(2, 0))
        spacer.pack_propagate(False)
        ctk.CTkLabel(
            header,
            text="Etiqueta",
            font=bold,
            width=160,
            anchor="w",
            text_color=BudgetUiTheme.TXT_PRI,
        ).pack(side="left", padx=(0, 4))

    def _append_summary_row(
        self,
        title: str,
        _label_id: str,
        budget_amt: float,
        spent: float,
        diff: float,
        color: str,
    ) -> None:
        assert self._summary_panel is not None
        row = ctk.CTkFrame(self._summary_panel, fg_color="transparent")
        row.pack(fill="x", padx=8, pady=2)
        self._mount_summary_swatch(row, color)
        self._mount_summary_title_cell(row, title)
        self._mount_summary_money_cells(row, budget_amt, spent, diff)

    def _mount_summary_swatch(self, row: ctk.CTkFrame, color: str) -> None:
        swatch = ctk.CTkFrame(
            row,
            fg_color=color or BudgetUiTheme.BORDER,
            corner_radius=3,
            width=10,
            height=22,
        )
        swatch.pack(side="left", padx=(2, 8), pady=4)
        swatch.pack_propagate(False)

    def _mount_summary_title_cell(self, row: ctk.CTkFrame, title: str) -> None:
        ctk.CTkLabel(
            row,
            text=title,
            width=160,
            anchor="w",
            justify="left",
            wraplength=152,
            font=ctk.CTkFont(size=12),
            text_color=BudgetUiTheme.TXT_PRI,
        ).pack(side="left", padx=(0, 4))

    def _mount_summary_money_cells(
        self,
        row: ctk.CTkFrame,
        budget_amt: float,
        spent: float,
        diff: float,
    ) -> None:
        self._mount_summary_diff_cell(row, spent, budget_amt, diff)
        self._mount_summary_spent_cell(row, spent)
        self._mount_summary_budget_cell(row, budget_amt)

    def _mount_summary_diff_cell(
        self,
        row: ctk.CTkFrame,
        spent: float,
        budget_amt: float,
        diff: float,
    ) -> None:
        tone = self._resolve_diff_tone(spent, budget_amt)
        ctk.CTkLabel(
            row,
            text=CurrencyPresenter.format_cop(diff),
            width=96,
            anchor="e",
            text_color=tone,
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(side="right", padx=(4, 4))

    def _resolve_diff_tone(self, spent: float, budget_amt: float) -> str:
        # Tolerance covers float drift on whole-peso COP amounts.
        eps = 0.5
        if spent <= eps:
            return BudgetUiTheme.TXT_PRI
        if spent > budget_amt + eps:
            return BudgetUiTheme.RED
        if abs(spent - budget_amt) <= eps:
            return BudgetUiTheme.GREEN
        return BudgetUiTheme.AMBER

    def _mount_summary_spent_cell(self, row: ctk.CTkFrame, spent: float) -> None:
        ctk.CTkLabel(
            row,
            text=CurrencyPresenter.format_cop(spent),
            width=96,
            anchor="e",
            text_color=BudgetUiTheme.TXT_PRI,
            font=ctk.CTkFont(size=12),
        ).pack(side="right", padx=(0, 4))

    def _mount_summary_budget_cell(self, row: ctk.CTkFrame, budget_amt: float) -> None:
        ctk.CTkLabel(
            row,
            text=CurrencyPresenter.format_cop(budget_amt),
            width=96,
            anchor="e",
            text_color=BudgetUiTheme.TXT_SEC,
            font=ctk.CTkFont(size=12),
        ).pack(side="right", padx=(0, 4))

    def _flatten_budget_labels(self, workspace: BudgetWorkspace) -> list[tuple[str, str, float, str]]:
        rows = []
        for cat in workspace.categories:
            tint = cat.color_dark.strip() or cat.color_light.strip() or BudgetUiTheme.ACCENT
            for lbl in cat.labels:
                title = lbl.title.strip() or "Etiqueta"
                rows.append((title, lbl.label_id, lbl.amount_cop, tint))
        return rows

    def _resolve_label_title(self, workspace: BudgetWorkspace, label_id: str) -> str:
        for cat in workspace.categories:
            for lbl in cat.labels:
                if lbl.label_id == label_id:
                    return lbl.title
        return "Etiqueta"

    def _receipt_caption(self, receipt: IncomeReceipt) -> str:
        memo = receipt.memo.strip()
        suffix = f" · {memo}" if memo else ""
        return f"{receipt.occurred_on}{suffix} · {CurrencyPresenter.format_cop(receipt.amount_cop)}"

    def _handle_new_receipt(self) -> None:
        dialog = DistributionReceiptDialog(self._dialog_parent())
        payload = dialog.show()
        if payload is None:
            return
        self._save_new_receipt(payload)

    def _save_new_receipt(self, payload: tuple[str, float, str]) -> None:
        day, amount, memo = payload
        try:
            receipt = self._ledger.add_receipt(day, amount, memo)
        except ValueError as exc:
            messagebox.showwarning("Ingreso", str(exc))
            return
        self._select_receipt_after_creation(receipt)

    def _select_receipt_after_creation(self, receipt: IncomeReceipt) -> None:
        month_key = receipt.occurred_on[:7]
        self._reload_month_menu(select_latest=False)
        if month_key in self._month_keys:
            self._month_var.set(month_key)
        self._reload_receipt_menu(select_first=False)
        caption = self._receipt_caption(receipt)
        if caption in self._caption_to_receipt:
            self._receipt_var.set(caption)
        self._refresh_views()

    def _handle_new_line(self) -> None:
        receipt_id = self._active_receipt_id()
        if receipt_id is None:
            messagebox.showinfo("Distribución", "Selecciona un ingreso válido.")
            return
        self._open_new_line_dialog(receipt_id)

    def _open_new_line_dialog(self, receipt_id: str) -> None:
        receipt = self._ledger.receipt_by_id(receipt_id)
        workspace = self._book.peek()
        dialog = DistributionLineDialog(self._dialog_parent(), workspace, receipt.occurred_on)
        payload = dialog.show()
        if payload is None:
            return
        self._save_new_line(receipt_id, workspace, payload)

    def _save_new_line(
        self,
        receipt_id: str,
        workspace: BudgetWorkspace,
        payload: tuple[str, str, float, str],
    ) -> None:
        day, label_id, amount, memo = payload
        try:
            self._ledger.add_line(receipt_id, label_id, day, amount, memo, workspace)
        except (ValueError, KeyError) as exc:
            messagebox.showwarning("Distribución", str(exc))
            return
        self._refresh_views()

    def _confirm_delete_line(self, line_id: str) -> None:
        if not messagebox.askyesno("Distribución", "¿Eliminar esta distribución?"):
            return
        try:
            self._ledger.delete_line(line_id)
        except KeyError:
            messagebox.showwarning("Distribución", "No se encontró el movimiento.")
            return
        self._refresh_views()

    def _handle_delete_receipt(self) -> None:
        receipt_id = self._active_receipt_id()
        if receipt_id is None:
            messagebox.showinfo("Distribución", "No hay ingreso seleccionado.")
            return
        if not messagebox.askyesno("Distribución", "¿Eliminar este ingreso y todas sus distribuciones?"):
            return
        self._delete_receipt_and_reload(receipt_id)

    def _delete_receipt_and_reload(self, receipt_id: str) -> None:
        try:
            self._ledger.delete_receipt(receipt_id)
        except KeyError:
            messagebox.showwarning("Distribución", "No se encontró el ingreso.")
            return
        self._reload_month_menu(select_latest=False)
        self._reload_receipt_menu(select_first=True)
        self._refresh_views()
