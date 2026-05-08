"""Manage CRUD for investment categories in one modal surface."""

from __future__ import annotations

from tkinter import messagebox

import customtkinter as ctk

from finanmind.models.investment_category import InvestmentCategory
from finanmind.services.investment_service import InvestmentService
from finanmind.ui.budget_ui_theme import BudgetUiTheme
from finanmind.ui.investment_category_editor_dialog import InvestmentCategoryEditorDialog


class InvestmentCategoriesManagerDialog:
    """Lists categories with add, rename, and delete actions."""

    def __init__(self, master: ctk.Misc, service: InvestmentService) -> None:
        self._master = master
        self._service = service
        self._win: ctk.CTkToplevel | None = None
        self._list_host: ctk.CTkScrollableFrame | None = None

    def show(self) -> None:
        """Open modally until the user closes the window."""
        self._spawn()
        assert self._win is not None
        self._master.wait_window(self._win)

    def _spawn(self) -> None:
        win = ctk.CTkToplevel(self._master)
        self._win = win
        win.title("Categorías de inversión")
        win.geometry("520x420")
        win.transient(self._master)
        win.grab_set()
        win.configure(fg_color=BudgetUiTheme.BG_CARD)
        self._build(win)

    def _build(self, win: ctk.CTkToplevel) -> None:
        shell = ctk.CTkFrame(win, fg_color=BudgetUiTheme.BG_CARD)
        shell.pack(fill="both", expand=True, padx=16, pady=16)
        self._header(shell)
        self._add_button(shell)
        self._mount_scroll(shell)
        self._close_button(shell)
        self._reload_rows()

    def _header(self, shell: ctk.CTkFrame) -> None:
        ctk.CTkLabel(
            shell,
            text="Tus categorías (nombre = activo en el que inviertes)",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=BudgetUiTheme.TXT_PRI,
        ).pack(anchor="w")

    def _add_button(self, shell: ctk.CTkFrame) -> None:
        ctk.CTkButton(
            shell,
            text="Nueva categoría",
            command=self._on_add,
            fg_color=BudgetUiTheme.ACCENT,
            hover_color=BudgetUiTheme.ACCENT_HOVER,
            text_color="#ffffff",
            height=32,
        ).pack(anchor="w", pady=(10, 8))

    def _mount_scroll(self, shell: ctk.CTkFrame) -> None:
        scroll = ctk.CTkScrollableFrame(
            shell,
            fg_color=BudgetUiTheme.BG_MAIN,
            height=240,
            corner_radius=8,
            border_width=1,
            border_color=BudgetUiTheme.BORDER,
        )
        scroll.pack(fill="both", expand=True, pady=(0, 10))
        self._list_host = scroll

    def _close_button(self, shell: ctk.CTkFrame) -> None:
        ctk.CTkButton(
            shell,
            text="Cerrar",
            command=self._close,
            height=32,
            fg_color=BudgetUiTheme.BG_MAIN,
            hover_color=BudgetUiTheme.BG_HOVER,
            border_width=1,
            border_color=BudgetUiTheme.BORDER,
            text_color=BudgetUiTheme.TXT_PRI,
        ).pack(anchor="e")

    def _reload_rows(self) -> None:
        assert self._list_host is not None
        for child in self._list_host.winfo_children():
            child.destroy()
        cats = self._service.categories_snapshot()
        if not cats:
            self._empty_hint()
            return
        for cat in sorted(cats, key=lambda c: c.name.lower()):
            self._render_row(cat)

    def _empty_hint(self) -> None:
        assert self._list_host is not None
        ctk.CTkLabel(
            self._list_host,
            text="Aún no hay categorías. Crea la primera para registrar inversiones.",
            text_color=BudgetUiTheme.TXT_SEC,
            font=ctk.CTkFont(size=12),
        ).pack(padx=12, pady=20)

    def _render_row(self, cat: InvestmentCategory) -> None:
        assert self._list_host is not None
        row = ctk.CTkFrame(self._list_host, fg_color=BudgetUiTheme.BG_CARD, corner_radius=8)
        row.pack(fill="x", padx=8, pady=4)
        ctk.CTkLabel(row, text=cat.name, text_color=BudgetUiTheme.TXT_PRI, font=ctk.CTkFont(size=13)).pack(
            side="left", padx=10, pady=8
        )
        ctk.CTkButton(row, text="Editar", width=72, command=lambda c=cat: self._on_edit(c)).pack(
            side="right", padx=(0, 6), pady=6
        )
        ctk.CTkButton(
            row,
            text="Eliminar",
            width=80,
            fg_color=BudgetUiTheme.RED,
            hover_color="#dc2626",
            command=lambda c=cat: self._on_delete(c),
        ).pack(side="right", padx=6, pady=6)

    def _on_add(self) -> None:
        dlg = InvestmentCategoryEditorDialog(self._win, "Nueva categoría", "")
        name = dlg.show()
        if not name:
            return
        try:
            self._service.add_category(name)
        except ValueError as exc:
            messagebox.showerror("Finanmind", str(exc))
            return
        except RuntimeError as exc:
            messagebox.showerror("Finanmind", str(exc))
            return
        self._reload_rows()

    def _on_edit(self, cat: InvestmentCategory) -> None:
        dlg = InvestmentCategoryEditorDialog(self._win, "Editar categoría", cat.name)
        name = dlg.show()
        if not name:
            return
        try:
            self._service.update_category(cat.category_id, name)
        except ValueError as exc:
            messagebox.showerror("Finanmind", str(exc))
            return
        except RuntimeError as exc:
            messagebox.showerror("Finanmind", str(exc))
            return
        self._reload_rows()

    def _on_delete(self, cat: InvestmentCategory) -> None:
        if not messagebox.askyesno("Finanmind", f"¿Eliminar la categoría «{cat.name}»?"):
            return
        try:
            self._service.delete_category(cat.category_id)
        except (ValueError, KeyError) as exc:
            messagebox.showerror("Finanmind", str(exc))
            return
        except RuntimeError as exc:
            messagebox.showerror("Finanmind", str(exc))
            return
        self._reload_rows()

    def _close(self) -> None:
        assert self._win is not None
        self._win.destroy()
