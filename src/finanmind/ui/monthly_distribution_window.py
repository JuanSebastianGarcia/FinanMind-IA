"""Monthly distribution ledger versus fixed budget labels."""

from __future__ import annotations

from datetime import date
from tkinter import messagebox

import customtkinter as ctk

from finanmind.models.budget_workspace import BudgetWorkspace
from finanmind.models.income_distribution_line import IncomeDistributionLine
from finanmind.models.income_receipt import IncomeReceipt
from finanmind.budget.book_service import BudgetBookService
from finanmind.services.monthly_distribution_service import MonthlyDistributionService
from finanmind.ui.budget_match_row_fill import BudgetMatchRowFill
from finanmind.ui.currency_presenter import CurrencyPresenter
from finanmind.ui.distribution_line_dialog import DistributionLineDialog
from finanmind.ui.distribution_receipt_dialog import DistributionReceiptDialog


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
        """Mount widgets and hydrate from disk."""
        self._book.load()
        self._ledger.load()
        shell = ctk.CTkFrame(self._host, fg_color="#FFFFFF")
        shell.pack(fill="both", expand=True, padx=22, pady=22)
        self._render_heading(shell)
        split = ctk.CTkFrame(shell, fg_color="transparent")
        split.pack(fill="both", expand=True, pady=(4, 0))
        left_rail = ctk.CTkFrame(split, fg_color="transparent")
        left_rail.pack(side="left", fill="both", expand=True, padx=(0, 14))
        right_rail = ctk.CTkFrame(split, fg_color="transparent", width=440)
        right_rail.pack(side="right", fill="both")
        right_rail.pack_propagate(False)
        self._render_controls(left_rail)
        self._render_ledger_region(left_rail)
        self._render_summary_region(right_rail)
        self._bootstrap_months()

    def _render_heading(self, shell: ctk.CTkFrame) -> None:
        title_font = ctk.CTkFont(size=26, weight="bold")
        title = ctk.CTkLabel(shell, text="Distribución mensual", font=title_font)
        title.pack(anchor="w")
        hint_font = ctk.CTkFont(size=14)
        hint = ctk.CTkLabel(
            shell,
            text="Registra ingresos y cómo se reparten en las etiquetas del presupuesto.",
            font=hint_font,
            text_color="#64748b",
        )
        hint.pack(anchor="w", pady=(6, 14))

    def _render_controls(self, rail: ctk.CTkFrame) -> None:
        row = ctk.CTkFrame(rail, fg_color="transparent")
        row.pack(fill="x")
        ctk.CTkLabel(row, text="Mes").pack(side="left")
        menu = ctk.CTkOptionMenu(row, variable=self._month_var, values=["—"], command=self._handle_month_pick)
        menu.pack(side="left", padx=(10, 18))
        self._month_menu = menu
        ctk.CTkButton(row, text="Nuevo ingreso", command=self._handle_new_receipt).pack(side="left", padx=(0, 10))
        row2 = ctk.CTkFrame(rail, fg_color="transparent")
        row2.pack(fill="x", pady=(12, 8))
        ctk.CTkLabel(row2, text="Ingreso seleccionado").pack(side="left")
        receipt_menu = ctk.CTkOptionMenu(
            row2,
            variable=self._receipt_var,
            values=["—"],
            command=self._handle_receipt_pick,
        )
        receipt_menu.pack(side="left", padx=(10, 18))
        self._receipt_menu = receipt_menu
        self._remainder_lbl = ctk.CTkLabel(row2, text="", font=ctk.CTkFont(size=15, weight="bold"))
        self._remainder_lbl.pack(side="left", padx=(8, 18))
        ctk.CTkButton(row2, text="Registrar distribución", command=self._handle_new_line).pack(side="left", padx=(0, 10))
        ctk.CTkButton(row2, text="Eliminar ingreso", fg_color="#dc2626", hover_color="#b91c1c", command=self._handle_delete_receipt).pack(
            side="left",
        )

    def _render_ledger_region(self, rail: ctk.CTkFrame) -> None:
        caption = ctk.CTkLabel(rail, text="Movimientos del ingreso", font=ctk.CTkFont(size=16, weight="bold"))
        caption.pack(anchor="w", pady=(10, 6))
        ledger = ctk.CTkScrollableFrame(rail, corner_radius=14, fg_color="#F8FAFC")
        ledger.pack(fill="both", expand=True)
        self._ledger_panel = ledger

    def _render_summary_region(self, rail: ctk.CTkFrame) -> None:
        panel = ctk.CTkFrame(rail, fg_color="#F1F5F9", corner_radius=14)
        panel.pack(fill="both", expand=True)
        inner = ctk.CTkFrame(panel, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=12, pady=12)
        caption = ctk.CTkLabel(
            inner,
            text="Resumen del mes vs presupuesto",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        caption.pack(anchor="w")
        hint = ctk.CTkLabel(
            inner,
            text="Contrasta lo distribuido en el mes con cada etiqueta.",
            font=ctk.CTkFont(size=12),
            text_color="#64748b",
        )
        hint.pack(anchor="w", pady=(2, 8))
        summary = ctk.CTkScrollableFrame(inner, fg_color="#FFFFFF", corner_radius=10)
        summary.pack(fill="both", expand=True)
        self._summary_panel = summary

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
            self._remainder_lbl.configure(text="Selecciona un ingreso", text_color="#64748b")
            return
        remainder = self._ledger.remaining_for_receipt(receipt_id)
        label = f"Por distribuir: {CurrencyPresenter.format_cop(remainder)}"
        tone = "#dc2626" if remainder < 0 else "#0f172a"
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
        balance = receipt.amount_cop
        self._append_ledger_header()
        self._append_income_row(receipt, balance)
        for ln in lines:
            balance -= ln.amount_cop
            self._append_line_row(receipt_id, ln, balance)

    def _render_empty_ledger(self, msg: str) -> None:
        assert self._ledger_panel is not None
        ctk.CTkLabel(self._ledger_panel, text=msg).pack(anchor="w", padx=12, pady=12)

    def _append_ledger_header(self) -> None:
        assert self._ledger_panel is not None
        row = ctk.CTkFrame(self._ledger_panel, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=(8, 4))
        self._grid_cell(row, "Fecha", bold=True, width=120)
        self._grid_cell(row, "Concepto", bold=True, width=220)
        self._grid_cell(row, "Monto", bold=True, width=140)
        self._grid_cell(row, "Saldo ingreso", bold=True, width=160)
        self._grid_cell(row, "", bold=True, width=90)

    def _append_income_row(self, receipt: IncomeReceipt, balance: float) -> None:
        assert self._ledger_panel is not None
        row = ctk.CTkFrame(self._ledger_panel, fg_color="#E0F2FE")
        row.pack(fill="x", padx=10, pady=4)
        memo = receipt.memo.strip()
        concept = "Ingreso registrado"
        if memo:
            concept = f"Ingreso · {memo}"
        self._grid_cell(row, receipt.occurred_on, width=120)
        self._grid_cell(row, concept, width=220)
        self._grid_cell(row, CurrencyPresenter.format_cop(receipt.amount_cop), width=140)
        self._grid_cell(row, CurrencyPresenter.format_cop(balance), width=160)
        self._grid_cell(row, "", width=90)

    def _append_line_row(self, receipt_id: str, ln: IncomeDistributionLine, balance: float) -> None:
        assert self._ledger_panel is not None
        row = ctk.CTkFrame(self._ledger_panel, fg_color="#FFFFFF")
        row.pack(fill="x", padx=10, pady=4)
        workspace = self._book.peek()
        title = self._resolve_label_title(workspace, ln.label_id)
        memo = ln.memo.strip()
        concept = title if memo == "" else f"{title} · {memo}"
        self._grid_cell(row, ln.occurred_on, width=120)
        self._grid_cell(row, concept, width=220)
        self._grid_cell(row, CurrencyPresenter.format_cop(ln.amount_cop), width=140)
        tone = "#dc2626" if balance < 0 else "#0f172a"
        bal_lbl = ctk.CTkLabel(row, text=CurrencyPresenter.format_cop(balance), width=160, anchor="w", text_color=tone)
        bal_lbl.pack(side="left", padx=6)
        del_btn = ctk.CTkButton(row, text="Quitar", width=86, command=lambda: self._confirm_delete_line(ln.line_id))
        del_btn.pack(side="left", padx=6)

    def _grid_cell(self, row: ctk.CTkFrame, text: str, width: int, bold: bool = False) -> None:
        font = ctk.CTkFont(weight="bold") if bold else ctk.CTkFont()
        lbl = ctk.CTkLabel(row, text=text, width=width, anchor="w", font=font)
        lbl.pack(side="left", padx=6)

    def _render_summary_rows(self) -> None:
        assert self._summary_panel is not None
        for child in self._summary_panel.winfo_children():
            child.destroy()
        month_key = self._month_var.get().strip()
        workspace = self._book.peek()
        spent_map = self._ledger.monthly_spent_by_label(month_key)
        header = ctk.CTkFrame(self._summary_panel, fg_color="transparent")
        header.pack(fill="x", padx=8, pady=(8, 4))
        self._grid_cell(header, "Etiqueta", bold=True, width=152)
        self._grid_cell(header, "Ppto.", bold=True, width=88)
        self._grid_cell(header, "Dist.", bold=True, width=88)
        self._grid_cell(header, "Diff.", bold=True, width=88)
        rows = self._flatten_budget_labels(workspace)
        if not rows:
            ctk.CTkLabel(self._summary_panel, text="Sin etiquetas en el presupuesto.").pack(anchor="w", padx=12, pady=10)
            return
        for title, label_id, budget_amt in rows:
            spent = spent_map.get(label_id, 0.0)
            diff = budget_amt - spent
            self._append_summary_row(title, budget_amt, spent, diff)

    def _append_summary_row(self, title: str, budget_amt: float, spent: float, diff: float) -> None:
        assert self._summary_panel is not None
        fill = BudgetMatchRowFill.hex(spent, budget_amt)
        row = ctk.CTkFrame(self._summary_panel, fg_color=fill)
        row.pack(fill="x", padx=8, pady=3)
        self._grid_cell(row, title, width=152)
        self._grid_cell(row, CurrencyPresenter.format_cop(budget_amt), width=88)
        self._grid_cell(row, CurrencyPresenter.format_cop(spent), width=88)
        tone = "#dc2626" if diff < 0 else "#15803d"
        diff_lbl = ctk.CTkLabel(row, text=CurrencyPresenter.format_cop(diff), width=88, anchor="w", text_color=tone)
        diff_lbl.pack(side="left", padx=6)

    def _flatten_budget_labels(self, workspace: BudgetWorkspace) -> list[tuple[str, str, float]]:
        rows = []
        for cat in workspace.categories:
            prefix = cat.title.strip()
            for lbl in cat.labels:
                title = f"{prefix} · {lbl.title}" if prefix else lbl.title
                rows.append((title, lbl.label_id, lbl.amount_cop))
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
        dialog = DistributionReceiptDialog(self._host)
        payload = dialog.show()
        if payload is None:
            return
        day, amount, memo = payload
        try:
            receipt = self._ledger.add_receipt(day, amount, memo)
        except ValueError as exc:
            messagebox.showwarning("Ingreso", str(exc))
            return
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
        receipt = self._ledger.receipt_by_id(receipt_id)
        workspace = self._book.peek()
        dialog = DistributionLineDialog(self._host, workspace, receipt.occurred_on)
        payload = dialog.show()
        if payload is None:
            return
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
        try:
            self._ledger.delete_receipt(receipt_id)
        except KeyError:
            messagebox.showwarning("Distribución", "No se encontró el ingreso.")
            return
        self._reload_month_menu(select_latest=False)
        self._reload_receipt_menu(select_first=True)
        self._refresh_views()
