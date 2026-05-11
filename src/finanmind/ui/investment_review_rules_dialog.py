"""Manage CRUD for personal investment review rules in one modal surface."""

from __future__ import annotations

from collections.abc import Callable
from tkinter import messagebox

import customtkinter as ctk

from finanmind.models.investment_review_rule import InvestmentReviewRule
from finanmind.services.investment_review_rules_store import (
    InvestmentReviewRulesStore,
)
from finanmind.ui.budget_ui_theme import BudgetUiTheme
from finanmind.ui.investment_review_rule_editor_dialog import (
    InvestmentReviewRuleEditorDialog,
)


class InvestmentReviewRulesDialog:
    """Lists rules with add, edit, and delete actions."""

    _WINDOW_SIZE = "640x520"
    _PREVIEW_CHARS = 220

    def __init__(
        self,
        master: ctk.Misc,
        store: InvestmentReviewRulesStore,
        on_changed: Callable[[], None] | None = None,
    ) -> None:
        self._master = master
        self._store = store
        self._on_changed = on_changed
        self._win: ctk.CTkToplevel | None = None
        self._list_host: ctk.CTkScrollableFrame | None = None

    def show(self) -> None:
        """Open the dialog modally."""
        self._spawn()
        assert self._win is not None
        self._master.wait_window(self._win)

    def _spawn(self) -> None:
        win = ctk.CTkToplevel(self._master)
        self._win = win
        win.title("Reglas personalizadas para la IA")
        win.geometry(self._WINDOW_SIZE)
        win.transient(self._master)
        win.grab_set()
        win.configure(fg_color=BudgetUiTheme.BG_MAIN)
        self._build(win)

    def _build(self, win: ctk.CTkToplevel) -> None:
        shell = ctk.CTkFrame(win, fg_color=BudgetUiTheme.BG_MAIN)
        shell.pack(fill="both", expand=True, padx=16, pady=16)
        self._header(shell)
        self._add_button(shell)
        self._mount_scroll(shell)
        self._close_button(shell)
        self._reload_rows()

    def _header(self, shell: ctk.CTkFrame) -> None:
        ctk.CTkLabel(
            shell,
            text="Contexto personal que se envía a la IA",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=BudgetUiTheme.TXT_PRI,
        ).pack(anchor="w")
        self._header_hint(shell)

    def _header_hint(self, shell: ctk.CTkFrame) -> None:
        hint = (
            "Agrega preferencias, objetivos, situación actual o cualquier dato "
            "personal. Cada regla se incluirá en el prompt cuando solicites un análisis."
        )
        ctk.CTkLabel(
            shell,
            text=hint,
            font=ctk.CTkFont(size=12),
            text_color=BudgetUiTheme.TXT_SEC,
            wraplength=580,
            justify="left",
            anchor="w",
        ).pack(anchor="w", pady=(2, 8))

    def _add_button(self, shell: ctk.CTkFrame) -> None:
        ctk.CTkButton(
            shell,
            text="Nueva regla",
            command=self._on_add,
            fg_color=BudgetUiTheme.ACCENT,
            hover_color=BudgetUiTheme.ACCENT_HOVER,
            text_color="#ffffff",
            height=32,
        ).pack(anchor="w", pady=(0, 8))

    def _mount_scroll(self, shell: ctk.CTkFrame) -> None:
        scroll = ctk.CTkScrollableFrame(
            shell,
            fg_color=BudgetUiTheme.BG_CARD,
            corner_radius=8,
            border_width=1,
            border_color=BudgetUiTheme.BORDER,
            scrollbar_button_color=BudgetUiTheme.BORDER,
            scrollbar_button_hover_color=BudgetUiTheme.TXT_TER,
        )
        scroll.pack(fill="both", expand=True, pady=(0, 10))
        self._list_host = scroll

    def _close_button(self, shell: ctk.CTkFrame) -> None:
        ctk.CTkButton(
            shell,
            text="Cerrar",
            command=self._close,
            height=32,
            fg_color=BudgetUiTheme.BG_CARD,
            hover_color=BudgetUiTheme.BG_HOVER,
            border_width=1,
            border_color=BudgetUiTheme.BORDER,
            text_color=BudgetUiTheme.TXT_PRI,
        ).pack(anchor="e")

    def _reload_rows(self) -> None:
        assert self._list_host is not None
        for child in self._list_host.winfo_children():
            child.destroy()
        rules = self._store.snapshot()
        if not rules:
            self._empty_hint()
            return
        for rule in rules:
            self._render_row(rule)

    def _empty_hint(self) -> None:
        assert self._list_host is not None
        ctk.CTkLabel(
            self._list_host,
            text="Aún no hay reglas. Crea la primera para personalizar el análisis.",
            text_color=BudgetUiTheme.TXT_SEC,
            font=ctk.CTkFont(size=12),
            wraplength=540,
            justify="left",
        ).pack(padx=12, pady=20)

    def _render_row(self, rule: InvestmentReviewRule) -> None:
        assert self._list_host is not None
        card = ctk.CTkFrame(
            self._list_host,
            fg_color=BudgetUiTheme.BG_MAIN,
            corner_radius=8,
            border_width=1,
            border_color=BudgetUiTheme.BORDER,
        )
        card.pack(fill="x", padx=8, pady=4)
        self._mount_row_text(card, rule)
        self._mount_row_actions(card, rule)

    def _mount_row_text(self, card: ctk.CTkFrame, rule: InvestmentReviewRule) -> None:
        preview = self._preview_text(rule.cleaned_text())
        ctk.CTkLabel(
            card,
            text=preview,
            text_color=BudgetUiTheme.TXT_PRI,
            font=ctk.CTkFont(size=12),
            wraplength=560,
            justify="left",
            anchor="w",
        ).pack(anchor="w", padx=12, pady=(10, 4), fill="x")

    def _mount_row_actions(self, card: ctk.CTkFrame, rule: InvestmentReviewRule) -> None:
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=8, pady=(0, 8))
        self._mount_edit_button(row, rule)
        self._mount_delete_button(row, rule)

    def _mount_edit_button(self, row: ctk.CTkFrame, rule: InvestmentReviewRule) -> None:
        ctk.CTkButton(
            row,
            text="Editar",
            width=72,
            height=28,
            command=lambda r=rule: self._on_edit(r),
            fg_color=BudgetUiTheme.BG_CARD,
            hover_color=BudgetUiTheme.BG_HOVER,
            border_width=1,
            border_color=BudgetUiTheme.BORDER,
            text_color=BudgetUiTheme.TXT_PRI,
        ).pack(side="right", padx=(0, 6))

    def _mount_delete_button(self, row: ctk.CTkFrame, rule: InvestmentReviewRule) -> None:
        ctk.CTkButton(
            row,
            text="Eliminar",
            width=80,
            height=28,
            fg_color=BudgetUiTheme.RED,
            hover_color="#dc2626",
            command=lambda r=rule: self._on_delete(r),
        ).pack(side="right")

    def _preview_text(self, raw: str) -> str:
        if len(raw) <= self._PREVIEW_CHARS:
            return raw
        return raw[: self._PREVIEW_CHARS - 1] + "…"

    def _on_add(self) -> None:
        dlg = InvestmentReviewRuleEditorDialog(self._win, "Nueva regla", "")
        text = dlg.show()
        if not text:
            return
        if not self._safe_mutate(lambda: self._store.add(text)):
            return
        self._reload_rows()
        self._notify_changed()

    def _on_edit(self, rule: InvestmentReviewRule) -> None:
        dlg = InvestmentReviewRuleEditorDialog(self._win, "Editar regla", rule.text)
        text = dlg.show()
        if not text:
            return
        if not self._safe_mutate(lambda: self._store.update(rule.rule_id, text)):
            return
        self._reload_rows()
        self._notify_changed()

    def _on_delete(self, rule: InvestmentReviewRule) -> None:
        if not messagebox.askyesno("Finanmind", "¿Eliminar esta regla?"):
            return
        if not self._safe_mutate(lambda: self._store.delete(rule.rule_id)):
            return
        self._reload_rows()
        self._notify_changed()

    def _safe_mutate(self, action: Callable[[], object]) -> bool:
        try:
            action()
        except (ValueError, KeyError) as exc:
            messagebox.showerror("Finanmind", str(exc))
            return False
        except RuntimeError as exc:
            messagebox.showerror("Finanmind", str(exc))
            return False
        return True

    def _notify_changed(self) -> None:
        if self._on_changed is not None:
            self._on_changed()

    def _close(self) -> None:
        if self._win is not None:
            self._win.destroy()
            self._win = None
