"""Interactive budget overview backed by CSV persistence."""

from __future__ import annotations

from tkinter import messagebox

import customtkinter as ctk

from finanmind.models.budget_category import BudgetCategory
from finanmind.models.budget_label import BudgetLabel
from finanmind.models.budget_workspace import BudgetWorkspace
from finanmind.budget.book_service import BudgetBookService
from finanmind.budget.salary_shares import BudgetSalaryShares
from finanmind.ui.budget_category_dialog import BudgetCategoryDialog
from finanmind.ui.budget_label_dialog import BudgetLabelDialog
from finanmind.ui.budget_salary_dialog import BudgetSalaryDialog
from finanmind.ui.currency_presenter import CurrencyPresenter
from finanmind.ui.percentage_presenter import PercentagePresenter


class BudgetManagementWindow:
    """Hosts CRUD controls plus horizontal category tables."""

    def __init__(self, host: ctk.CTkFrame, book: BudgetBookService) -> None:
        self._host = host
        self._book = book
        self._salary_lbl: ctk.CTkLabel | None = None
        self._scroll: ctk.CTkScrollableFrame | None = None

    def attach(self) -> None:
        """Mount widgets and hydrate from disk."""
        self._book.load()
        outer = ctk.CTkFrame(self._host, fg_color="#FFFFFF")
        outer.pack(fill="both", expand=True, padx=22, pady=22)
        self._render_title_block(outer)
        self._render_toolbar(outer)
        self._render_salary_band(outer)
        self._render_hint(outer)
        self._mount_scroll_region(outer)
        self.refresh()

    def refresh(self) -> None:
        """Reload salary caption and rebuild tables."""
        self._sync_salary_text()
        self._rebuild_tables()

    def _render_title_block(self, outer: ctk.CTkFrame) -> None:
        font = ctk.CTkFont(size=26, weight="bold")
        title = ctk.CTkLabel(outer, text="Gestión del presupuesto", font=font)
        title.pack(anchor="w")

    def _render_toolbar(self, outer: ctk.CTkFrame) -> None:
        row = ctk.CTkFrame(outer, fg_color="transparent")
        row.pack(fill="x", pady=(10, 0))
        add_btn = ctk.CTkButton(row, text="Agregar categoría", command=self._handle_new_category)
        add_btn.pack(side="left")

    def _render_salary_band(self, outer: ctk.CTkFrame) -> None:
        bar = ctk.CTkFrame(outer, fg_color="#EFF3F8", corner_radius=14)
        bar.pack(fill="x", pady=(12, 14))
        inner = ctk.CTkFrame(bar, fg_color="transparent")
        inner.pack(fill="x", padx=18, pady=14)
        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack(fill="x")
        self._salary_lbl = ctk.CTkLabel(row, text="", font=ctk.CTkFont(size=18, weight="bold"))
        self._salary_lbl.pack(side="left")
        edit_btn = ctk.CTkButton(row, text="Editar salario", command=self._handle_edit_salary)
        edit_btn.pack(side="right")

    def _render_hint(self, outer: ctk.CTkFrame) -> None:
        hint_font = ctk.CTkFont(size=14)
        caption = "Datos en COP · porcentajes vs salario · guardado en budget.csv"
        hint = ctk.CTkLabel(outer, text=caption, font=hint_font, text_color="#64748b")
        hint.pack(anchor="w", pady=(0, 12))

    def _mount_scroll_region(self, outer: ctk.CTkFrame) -> None:
        scroll = ctk.CTkScrollableFrame(
            outer,
            orientation="horizontal",
            corner_radius=16,
            fg_color="#F4F6FA",
            height=460,
        )
        scroll.pack(fill="both", expand=True)
        self._scroll = scroll

    def _sync_salary_text(self) -> None:
        workspace = self._book.peek()
        label_text = f"Salario actual · {CurrencyPresenter.format_cop(workspace.salary_cop)}"
        assert self._salary_lbl is not None
        self._salary_lbl.configure(text=label_text)

    def _rebuild_tables(self) -> None:
        assert self._scroll is not None
        for child in self._scroll.winfo_children():
            child.destroy()
        workspace = self._book.peek()
        shares = self._percent_by_category(workspace)
        if not workspace.categories:
            self._render_empty_state()
            return
        for cat in workspace.categories:
            pct = shares.get(cat.category_id, 0.0)
            self._render_category_column(cat, pct)

    def _percent_by_category(self, workspace: BudgetWorkspace) -> dict[str, float]:
        pairs = [(c.category_id, [lbl.amount_cop for lbl in c.labels]) for c in workspace.categories]
        return BudgetSalaryShares.map_by_category(workspace.salary_cop, pairs)

    def _render_empty_state(self) -> None:
        assert self._scroll is not None
        msg = 'Sin categorías todavía. Pulsa "Agregar categoría".'
        label = ctk.CTkLabel(self._scroll, text=msg)
        label.pack(padx=24, pady=36)

    def _render_category_column(self, cat: BudgetCategory, pct: float) -> None:
        assert self._scroll is not None
        card = ctk.CTkFrame(self._scroll, width=320, corner_radius=14, fg_color=cat.color_light)
        card.pack(side="left", padx=(0, 16), pady=14, fill="y")
        card.pack_propagate(False)
        self._render_category_toolbar(card, cat)
        self._render_category_banner(card, cat.title, pct)
        self._render_grid_header(card)
        for label in cat.labels:
            self._render_label_row(card, cat.category_id, label)

    def _render_category_toolbar(self, card: ctk.CTkFrame, cat: BudgetCategory) -> None:
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=(10, 4))
        add_cmd = lambda cid=cat.category_id: self._handle_add_label(cid)
        edit_cmd = lambda c=cat: self._handle_edit_category(c)
        del_cmd = lambda cid=cat.category_id: self._handle_delete_category(cid)
        ctk.CTkButton(row, text="+ Etiqueta", width=96, height=28, command=add_cmd).pack(side="left", padx=2)
        ctk.CTkButton(row, text="Editar", width=74, height=28, command=edit_cmd).pack(side="left", padx=2)
        ctk.CTkButton(
            row,
            text="Eliminar",
            width=82,
            height=28,
            fg_color="#dc2626",
            hover_color="#b91c1c",
            command=del_cmd,
        ).pack(side="left", padx=2)

    def _render_category_banner(self, card: ctk.CTkFrame, title: str, pct: float) -> None:
        pct_piece = PercentagePresenter.format_pct(pct)
        heading = f"{title} · {pct_piece} del salario"
        font = ctk.CTkFont(size=15, weight="bold")
        label = ctk.CTkLabel(
            card,
            text=heading,
            font=font,
            text_color="#0f172a",
            justify="left",
            wraplength=270,
        )
        label.pack(anchor="w", padx=14, pady=(6, 10))

    def _render_grid_header(self, card: ctk.CTkFrame) -> None:
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=(0, 6))
        header_font = ctk.CTkFont(size=12, weight="bold")
        left = ctk.CTkLabel(row, text="Etiqueta", font=header_font, width=118, anchor="w")
        left.pack(side="left", padx=(4, 6))
        right = ctk.CTkLabel(row, text="Importe", font=header_font, width=102, anchor="e")
        right.pack(side="left", padx=(0, 72))
        rule = ctk.CTkFrame(card, height=2, fg_color="#CBD5E1")
        rule.pack(fill="x", padx=12, pady=(0, 10))

    def _render_label_row(self, card: ctk.CTkFrame, category_id: str, label: BudgetLabel) -> None:
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=8, pady=4)
        self._render_label_cells(row, label)
        self._render_label_buttons(row, category_id, label)

    def _render_label_cells(self, row: ctk.CTkFrame, label: BudgetLabel) -> None:
        body_font = ctk.CTkFont(size=13)
        name_lbl = ctk.CTkLabel(row, text=label.title, font=body_font, width=118, anchor="w")
        name_lbl.pack(side="left", padx=(4, 6))
        amt_lbl = ctk.CTkLabel(
            row,
            text=CurrencyPresenter.format_cop(label.amount_cop),
            font=body_font,
            width=102,
            anchor="e",
        )
        amt_lbl.pack(side="left", padx=(0, 6))

    def _render_label_buttons(self, row: ctk.CTkFrame, category_id: str, label: BudgetLabel) -> None:
        edit_cmd = lambda cid=category_id, lbl=label: self._handle_edit_label(cid, lbl)
        del_cmd = lambda cid=category_id, lid=label.label_id: self._handle_delete_label(cid, lid)
        ctk.CTkButton(row, text="✎", width=32, height=26, command=edit_cmd).pack(side="left", padx=2)
        ctk.CTkButton(row, text="✕", width=32, height=26, fg_color="#94a3b8", command=del_cmd).pack(side="left")

    def _handle_new_category(self) -> None:
        palette = self._book.next_palette()
        dlg = BudgetCategoryDialog(self._dialog_parent(), "", palette)
        payload = dlg.show()
        if payload is None:
            return
        try:
            self._book.add_category(payload[0], payload[1])
        except ValueError as exc:
            messagebox.showerror("Categoría", str(exc))
            return
        self.refresh()

    def _handle_edit_category(self, cat: BudgetCategory) -> None:
        seed = cat.color_light.strip() or cat.color_dark.strip()
        dlg = BudgetCategoryDialog(self._dialog_parent(), cat.title, seed)
        payload = dlg.show()
        if payload is None:
            return
        try:
            self._book.update_category(cat.category_id, payload[0], payload[1])
        except (ValueError, KeyError) as exc:
            messagebox.showerror("Categoría", str(exc))
            return
        self.refresh()

    def _handle_delete_category(self, category_id: str) -> None:
        prompt = "¿Eliminar la categoría y todas sus etiquetas?"
        if not messagebox.askyesno("Eliminar categoría", prompt):
            return
        try:
            self._book.delete_category(category_id)
        except KeyError:
            messagebox.showerror("Categoría", "No se encontró la categoría.")
            return
        self.refresh()

    def _handle_edit_salary(self) -> None:
        workspace = self._book.peek()
        dlg = BudgetSalaryDialog(self._dialog_parent(), workspace.salary_cop)
        value = dlg.show()
        if value is None:
            return
        try:
            self._book.set_salary_cop(value)
        except ValueError as exc:
            messagebox.showerror("Salario", str(exc))
            return
        self.refresh()

    def _handle_add_label(self, category_id: str) -> None:
        dlg = BudgetLabelDialog(self._dialog_parent(), "", 0.0)
        payload = dlg.show()
        if payload is None:
            return
        try:
            self._book.add_label(category_id, payload[0], payload[1])
        except (ValueError, KeyError) as exc:
            messagebox.showerror("Etiqueta", str(exc))
            return
        self.refresh()

    def _handle_edit_label(self, category_id: str, label: BudgetLabel) -> None:
        dlg = BudgetLabelDialog(self._dialog_parent(), label.title, label.amount_cop)
        payload = dlg.show()
        if payload is None:
            return
        try:
            self._book.update_label(category_id, label.label_id, payload[0], payload[1])
        except (ValueError, KeyError) as exc:
            messagebox.showerror("Etiqueta", str(exc))
            return
        self.refresh()

    def _handle_delete_label(self, category_id: str, label_id: str) -> None:
        if not messagebox.askyesno("Eliminar etiqueta", "¿Eliminar esta etiqueta?"):
            return
        try:
            self._book.delete_label(category_id, label_id)
        except KeyError:
            messagebox.showerror("Etiqueta", "No se encontró la etiqueta.")
            return
        self.refresh()

    def _dialog_parent(self) -> ctk.Misc:
        return self._host.winfo_toplevel()
