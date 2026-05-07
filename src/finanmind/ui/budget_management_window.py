"""Interactive budget overview backed by CSV persistence."""

from __future__ import annotations

import tkinter as tk
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
from finanmind.ui.budget_ui_theme import BudgetUiTheme
from finanmind.ui.currency_presenter import CurrencyPresenter
from finanmind.ui.percentage_presenter import PercentagePresenter


class BudgetManagementWindow:
    """Hosts CRUD controls plus horizontal category tables."""

    def __init__(self, host: ctk.CTkFrame, book: BudgetBookService) -> None:
        self._host = host
        self._book = book
        self._salary_primary_lbl: ctk.CTkLabel | None = None
        self._salary_sub_lbl: ctk.CTkLabel | None = None
        self._salary_badge_lbl: ctk.CTkLabel | None = None
        self._scroll: ctk.CTkScrollableFrame | None = None

    def attach(self) -> None:
        """Mount widgets and hydrate from disk."""
        self._book.load()
        outer = ctk.CTkFrame(self._host, fg_color=BudgetUiTheme.BG_MAIN)
        outer.pack(fill="both", expand=True, padx=20, pady=14)
        self._render_topbar(outer)
        self._mount_salary_card(outer)
        self._render_hint(outer)
        self._mount_scroll_region(outer)
        self.refresh()

    def refresh(self) -> None:
        """Reload salary caption and rebuild tables."""
        self._sync_salary_text()
        self._rebuild_tables()

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
        self._pack_topbar_heading(bar)
        self._pack_topbar_add_button(bar)
        self._pack_topbar_edit_salary_button(bar)

    def _pack_topbar_heading(self, bar: ctk.CTkFrame) -> None:
        font = ctk.CTkFont(size=16, weight="bold")
        title = ctk.CTkLabel(bar, text="Gestión del presupuesto", font=font, text_color=BudgetUiTheme.TXT_PRI)
        title.pack(side="left", padx=20, pady=14)

    def _pack_topbar_add_button(self, bar: ctk.CTkFrame) -> None:
        btn = ctk.CTkButton(
            bar,
            text="Agregar categoría",
            command=self._handle_new_category,
            fg_color=BudgetUiTheme.ACCENT,
            hover_color=BudgetUiTheme.ACCENT_HOVER,
            text_color="#ffffff",
            corner_radius=8,
            font=ctk.CTkFont(size=13),
            height=32,
        )
        btn.pack(side="right", padx=(6, 20), pady=12)

    def _pack_topbar_edit_salary_button(self, bar: ctk.CTkFrame) -> None:
        btn = ctk.CTkButton(
            bar,
            text="Editar salario",
            command=self._handle_edit_salary,
            fg_color="transparent",
            border_width=1,
            border_color=BudgetUiTheme.BORDER,
            text_color=BudgetUiTheme.TXT_SEC,
            hover_color=BudgetUiTheme.BG_HOVER,
            corner_radius=8,
            font=ctk.CTkFont(size=13),
            height=32,
        )
        btn.pack(side="right", padx=0, pady=12)

    def _mount_salary_card(self, outer: ctk.CTkFrame) -> None:
        card = ctk.CTkFrame(
            outer,
            fg_color=BudgetUiTheme.BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=BudgetUiTheme.BORDER,
        )
        card.pack(fill="x", pady=(14, 0))
        self._mount_salary_left_column(card)
        self._mount_salary_badge_column(card)

    def _mount_salary_left_column(self, card: ctk.CTkFrame) -> None:
        left = ctk.CTkFrame(card, fg_color="transparent")
        left.pack(side="left", padx=18, pady=14)
        self._mount_salary_icon(left)
        texts = ctk.CTkFrame(left, fg_color="transparent")
        texts.pack(side="left")
        big = ctk.CTkFont(size=20, weight="bold")
        self._salary_primary_lbl = ctk.CTkLabel(texts, text="", font=big, text_color=BudgetUiTheme.TXT_PRI)
        self._salary_primary_lbl.pack(anchor="w")
        small = ctk.CTkFont(size=11)
        self._salary_sub_lbl = ctk.CTkLabel(texts, text="", font=small, text_color=BudgetUiTheme.TXT_SEC)
        self._salary_sub_lbl.pack(anchor="w")

    def _mount_salary_badge_column(self, card: ctk.CTkFrame) -> None:
        right = ctk.CTkFrame(card, fg_color="transparent")
        right.pack(side="right", padx=18, pady=14)
        badge_font = ctk.CTkFont(size=11, weight="bold")
        self._salary_badge_lbl = ctk.CTkLabel(right, text="", corner_radius=20, font=badge_font, padx=10, pady=3)
        self._salary_badge_lbl.pack()

    def _mount_salary_icon(self, left: ctk.CTkFrame) -> None:
        icon_bg = ctk.CTkFrame(
            left,
            fg_color=BudgetUiTheme.ICON_SALARY_BG,
            corner_radius=10,
            width=40,
            height=40,
        )
        icon_bg.pack(side="left", padx=(0, 14))
        icon_bg.pack_propagate(False)
        ctk.CTkLabel(icon_bg, text="💰", font=ctk.CTkFont(size=18)).place(relx=0.5, rely=0.5, anchor="center")

    def _render_hint(self, outer: ctk.CTkFrame) -> None:
        caption = "Datos en COP · porcentajes vs salario · budget.csv"
        hint = ctk.CTkLabel(outer, text=caption, font=ctk.CTkFont(size=12), text_color=BudgetUiTheme.TXT_SEC)
        hint.pack(anchor="w", pady=(10, 12))

    def _mount_scroll_region(self, outer: ctk.CTkFrame) -> None:
        scroll = ctk.CTkScrollableFrame(
            outer,
            orientation="horizontal",
            corner_radius=16,
            fg_color="transparent",
            height=460,
            scrollbar_button_color=BudgetUiTheme.BORDER,
            scrollbar_button_hover_color=BudgetUiTheme.TXT_TER,
        )
        scroll.pack(fill="both", expand=True)
        self._scroll = scroll

    def _sync_salary_text(self) -> None:
        workspace = self._book.peek()
        primary, sub, badge, bg, fg = self._build_salary_summary(workspace)
        assert self._salary_primary_lbl and self._salary_sub_lbl and self._salary_badge_lbl
        self._salary_primary_lbl.configure(text=primary)
        self._salary_sub_lbl.configure(text=sub)
        self._salary_badge_lbl.configure(text=badge, fg_color=bg, text_color=fg)

    def _build_salary_summary(self, workspace: BudgetWorkspace) -> tuple[str, str, str, str, str]:
        pairs = self._workspace_label_pairs(workspace)
        salary = workspace.salary_cop
        total = BudgetSalaryShares.total_allocated_cop(pairs)
        used_pct = BudgetSalaryShares.amount_share_percent(salary, total)
        avail = BudgetSalaryShares.remaining_cop(salary, pairs)
        free_pct = BudgetSalaryShares.amount_share_percent(salary, avail)
        primary = CurrencyPresenter.format_cop(salary)
        sub = f"{CurrencyPresenter.format_cop(avail)} disponibles · {PercentagePresenter.format_pct(free_pct)} libre"
        badge = f"{PercentagePresenter.format_pct(used_pct)} asignado"
        over_budget = total > salary and salary > 0
        bg = BudgetUiTheme.BADGE_WARN_BG if over_budget else BudgetUiTheme.BADGE_OK_BG
        fg = BudgetUiTheme.BADGE_WARN_FG if over_budget else BudgetUiTheme.BADGE_OK_FG
        return primary, sub, badge, bg, fg

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
            self._render_category_column(cat, pct, workspace.salary_cop)

    def _workspace_label_pairs(self, workspace: BudgetWorkspace) -> list[tuple[str, list[float]]]:
        return [(c.category_id, [lbl.amount_cop for lbl in c.labels]) for c in workspace.categories]

    def _percent_by_category(self, workspace: BudgetWorkspace) -> dict[str, float]:
        return BudgetSalaryShares.map_by_category(workspace.salary_cop, self._workspace_label_pairs(workspace))

    def _render_empty_state(self) -> None:
        assert self._scroll is not None
        msg = 'Sin categorías todavía. Pulsa "Agregar categoría".'
        label = ctk.CTkLabel(self._scroll, text=msg, text_color=BudgetUiTheme.TXT_SEC)
        label.pack(padx=24, pady=36)

    def _render_category_column(self, cat: BudgetCategory, pct: float, salary_cop: float) -> None:
        card = self._open_category_card()
        accent = self._category_accent(cat)
        total = sum(lbl.amount_cop for lbl in cat.labels)
        self._render_category_header_row(card, cat, accent)
        self._mount_category_stats_row(card, pct, total)
        self._mount_category_progress_bar(card, pct, accent)
        self._mount_category_separator(card)
        self._render_grid_header(card)
        self._render_category_label_list(card, cat, salary_cop, accent)

    def _open_category_card(self) -> ctk.CTkFrame:
        assert self._scroll is not None
        card = ctk.CTkFrame(
            self._scroll,
            width=412,
            corner_radius=12,
            fg_color=BudgetUiTheme.BG_CARD,
            border_width=1,
            border_color=BudgetUiTheme.BORDER,
        )
        card.pack(side="left", padx=(0, 16), pady=14, fill="y")
        card.pack_propagate(False)
        return card

    def _category_accent(self, cat: BudgetCategory) -> str:
        return cat.color_dark.strip() or cat.color_light.strip() or BudgetUiTheme.ACCENT

    def _render_category_header_row(self, card: ctk.CTkFrame, cat: BudgetCategory, accent: str) -> None:
        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=14, pady=(12, 0))
        title_row = ctk.CTkFrame(hdr, fg_color="transparent")
        title_row.pack(fill="x")
        self._paint_category_dot(title_row, accent)
        self._pack_category_heading_cell(title_row, cat)
        self._pack_category_action_buttons(title_row, cat)

    def _pack_category_heading_cell(self, title_row: ctk.CTkFrame, cat: BudgetCategory) -> None:
        head_font = ctk.CTkFont(size=10, weight="bold")
        ctk.CTkLabel(title_row, text=cat.title.upper(), font=head_font, text_color=BudgetUiTheme.TXT_PRI, anchor="w").pack(
            side="left",
        )

    def _pack_category_action_buttons(self, title_row: ctk.CTkFrame, cat: BudgetCategory) -> None:
        acts = ctk.CTkFrame(title_row, fg_color="transparent")
        acts.pack(side="right")
        add_cmd = lambda cid=cat.category_id: self._handle_add_label(cid)
        edit_cmd = lambda c=cat: self._handle_edit_category(c)
        del_cmd = lambda cid=cat.category_id: self._handle_delete_category(cid)
        bg_add, fg_add = BudgetUiTheme.BTN_ADD_LABEL_BG, BudgetUiTheme.BTN_ADD_LABEL_FG
        self._small_card_btn(acts, "+ Etiqueta", bg_add, fg_add, add_cmd).pack(side="left", padx=2)
        self._small_card_btn(acts, "Editar", BudgetUiTheme.BG_MAIN, BudgetUiTheme.TXT_SEC, edit_cmd).pack(side="left", padx=2)
        self._small_card_btn(acts, "Eliminar", "#fee2e2", BudgetUiTheme.RED, del_cmd).pack(side="left", padx=2)

    def _paint_category_dot(self, title_row: ctk.CTkFrame, accent: str) -> None:
        dot = tk.Canvas(title_row, width=9, height=9, bg=BudgetUiTheme.BG_CARD, highlightthickness=0)
        dot.pack(side="left", padx=(0, 6))
        dot.create_oval(1, 1, 8, 8, fill=accent, outline="")

    def _small_card_btn(self, parent: ctk.Misc, text: str, bg: str, fg: str, cmd) -> ctk.CTkButton:
        return ctk.CTkButton(
            parent,
            text=text,
            command=cmd,
            height=20,
            font=ctk.CTkFont(size=10),
            fg_color=bg,
            text_color=fg,
            hover_color=bg,
            corner_radius=5,
            border_width=0,
        )

    def _mount_category_stats_row(self, card: ctk.CTkFrame, pct: float, total: float) -> None:
        pct_frame = ctk.CTkFrame(card, fg_color="transparent")
        pct_frame.pack(fill="x", padx=14, pady=(6, 0))
        body = f"{pct:.1f}".replace(".", ",")
        ctk.CTkLabel(pct_frame, text=body, font=ctk.CTkFont(size=22), text_color=BudgetUiTheme.TXT_PRI).pack(side="left")
        tail = f"% del salario  ·  {CurrencyPresenter.format_cop(total)}"
        ctk.CTkLabel(pct_frame, text=tail, font=ctk.CTkFont(size=11), text_color=BudgetUiTheme.TXT_SEC).pack(
            side="left",
            padx=(3, 0),
        )

    def _mount_category_progress_bar(self, card: ctk.CTkFrame, pct: float, accent: str) -> None:
        bar_bg = ctk.CTkFrame(card, fg_color=BudgetUiTheme.BG_MAIN, height=8, corner_radius=4)
        bar_bg.pack(fill="x", padx=14, pady=(4, 0))
        card.update_idletasks()
        span = max(bar_bg.winfo_width(), bar_bg.winfo_reqwidth())
        fill_w = max(1, int(span * min(100.0, pct) / 100.0))
        fill = ctk.CTkFrame(bar_bg, fg_color=accent, height=8, width=fill_w, corner_radius=4)
        fill.place(x=0, y=0)

    def _mount_category_separator(self, card: ctk.CTkFrame) -> None:
        ctk.CTkFrame(card, fg_color=BudgetUiTheme.BORDER, height=1).pack(fill="x", padx=0, pady=(8, 0))

    def _render_category_label_list(
        self,
        card: ctk.CTkFrame,
        cat: BudgetCategory,
        salary_cop: float,
        accent: str,
    ) -> None:
        list_body = ctk.CTkScrollableFrame(
            card,
            orientation="vertical",
            fg_color="transparent",
            corner_radius=0,
            scrollbar_button_color=BudgetUiTheme.BORDER,
            scrollbar_button_hover_color=BudgetUiTheme.TXT_TER,
        )
        list_body.pack(fill="both", expand=True, padx=0, pady=4)
        for label in cat.labels:
            self._render_label_row(list_body, cat.category_id, label, salary_cop, accent)

    def _render_grid_header(self, card: ctk.CTkFrame) -> None:
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=(0, 6))
        self._fill_grid_header_row(row)
        rule = ctk.CTkFrame(card, height=1, fg_color=BudgetUiTheme.BORDER)
        rule.pack(fill="x", padx=12, pady=(0, 10))

    def _fill_grid_header_row(self, row: ctk.CTkFrame) -> None:
        header_font = ctk.CTkFont(size=12, weight="bold")
        self._pack_label_action_strip(row)
        amt_hdr = ctk.CTkLabel(
            row,
            text="Importe / %",
            font=header_font,
            width=168,
            anchor="e",
            text_color=BudgetUiTheme.TXT_PRI,
        )
        amt_hdr.pack(side="right", padx=(0, 4))
        self._pack_grid_mini_spacer(row)
        name_hdr = ctk.CTkLabel(
            row,
            text="Etiqueta",
            font=header_font,
            width=136,
            anchor="w",
            text_color=BudgetUiTheme.TXT_PRI,
        )
        name_hdr.pack(side="left", padx=(4, 6))

    def _pack_grid_mini_spacer(self, row: ctk.CTkFrame) -> None:
        mini = ctk.CTkFrame(row, fg_color="transparent", width=44, height=28)
        mini.pack(side="left", padx=(4, 0))
        mini.pack_propagate(False)

    def _pack_label_action_strip(self, row: ctk.CTkFrame) -> None:
        strip = ctk.CTkFrame(row, fg_color="transparent", width=52, height=28)
        strip.pack(side="right", padx=(4, 0))
        strip.pack_propagate(False)

    def _render_label_row(
        self,
        card: ctk.CTkFrame,
        category_id: str,
        label: BudgetLabel,
        salary_cop: float,
        accent: str,
    ) -> None:
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=8, pady=4)
        self._render_label_buttons(row, category_id, label)
        self._render_label_amount_cell(row, label, salary_cop)
        self._render_label_mini_bar(row, label, salary_cop, accent)
        self._render_label_name_cell(row, label)

    def _render_label_mini_bar(
        self,
        row: ctk.CTkFrame,
        label: BudgetLabel,
        salary_cop: float,
        accent: str,
    ) -> None:
        share = (min(1.0, label.amount_cop / salary_cop * 5.0)) if salary_cop > 0 else 0.0
        bw = max(4, int(32 * share))
        bar_bg = ctk.CTkFrame(row, fg_color=BudgetUiTheme.BG_MAIN, width=32, height=5, corner_radius=2)
        bar_bg.pack(side="left", padx=(6, 6), pady=10)
        bar_bg.pack_propagate(False)
        fill = ctk.CTkFrame(bar_bg, fg_color=accent, width=bw, height=5, corner_radius=2)
        fill.place(x=0, y=0)

    def _render_label_name_cell(self, row: ctk.CTkFrame, label: BudgetLabel) -> None:
        name_lbl = ctk.CTkLabel(
            row,
            text=label.title,
            font=ctk.CTkFont(size=11),
            text_color=BudgetUiTheme.TXT_SEC,
            width=136,
            anchor="w",
            justify="left",
            wraplength=128,
        )
        name_lbl.pack(side="left", padx=(4, 6))

    def _render_label_amount_cell(self, row: ctk.CTkFrame, label: BudgetLabel, salary_cop: float) -> None:
        share = BudgetSalaryShares.amount_share_percent(salary_cop, label.amount_cop)
        amt_text = f"{CurrencyPresenter.format_cop(label.amount_cop)} · {PercentagePresenter.format_pct(share)}"
        amt_lbl = ctk.CTkLabel(
            row,
            text=amt_text,
            font=ctk.CTkFont(size=11, weight="bold"),
            width=168,
            anchor="e",
            text_color=BudgetUiTheme.TXT_PRI,
        )
        amt_lbl.pack(side="right", padx=(0, 4))

    def _render_label_buttons(self, row: ctk.CTkFrame, category_id: str, label: BudgetLabel) -> None:
        strip = ctk.CTkFrame(row, fg_color="transparent", width=52, height=28)
        strip.pack(side="right", padx=(4, 0))
        strip.pack_propagate(False)
        edit_cmd = lambda cid=category_id, lbl=label: self._handle_edit_label(cid, lbl)
        del_cmd = lambda cid=category_id, lid=label.label_id: self._handle_delete_label(cid, lid)
        self._outline_icon_btn(strip, "✎", edit_cmd).pack(side="left", padx=(0, 2))
        self._outline_icon_btn(strip, "✕", del_cmd, hover="#fee2e2").pack(side="left")

    def _outline_icon_btn(self, parent: ctk.Misc, text: str, cmd, hover: str | None = None) -> ctk.CTkButton:
        hov = hover or BudgetUiTheme.BG_HOVER
        font = ctk.CTkFont(size=10)
        return ctk.CTkButton(
            parent,
            text=text,
            width=22,
            height=22,
            command=cmd,
            fg_color="transparent",
            border_width=1,
            border_color=BudgetUiTheme.BORDER,
            text_color=BudgetUiTheme.TXT_TER,
            hover_color=hov,
            corner_radius=5,
            font=font,
        )

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
