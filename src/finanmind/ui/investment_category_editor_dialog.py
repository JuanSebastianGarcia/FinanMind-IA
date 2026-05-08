"""Modal dialog to create or rename a single investment category."""

from __future__ import annotations

import customtkinter as ctk

from finanmind.ui.budget_ui_theme import BudgetUiTheme


class InvestmentCategoryEditorDialog:
    """Collects a category title; returns the trimmed value when confirmed."""

    def __init__(self, master: ctk.Misc, window_title: str, seed_name: str) -> None:
        self._master = master
        self._window_title = window_title
        self._seed = seed_name
        self._result: str | None = None
        self._win: ctk.CTkToplevel | None = None
        self._entry: ctk.CTkEntry | None = None

    def show(self) -> str | None:
        """Block until closed; return the name or ``None`` when cancelled."""
        self._open_window()
        assert self._win is not None
        self._master.wait_window(self._win)
        return self._result

    def _open_window(self) -> None:
        win = ctk.CTkToplevel(self._master)
        self._win = win
        win.title(self._window_title)
        win.geometry("420x200")
        win.transient(self._master)
        win.grab_set()
        win.configure(fg_color=BudgetUiTheme.BG_CARD)
        self._build_shell(win)

    def _build_shell(self, win: ctk.CTkToplevel) -> None:
        shell = ctk.CTkFrame(win, fg_color=BudgetUiTheme.BG_CARD)
        shell.pack(fill="both", expand=True, padx=18, pady=18)
        self._mount_label(shell)
        self._mount_entry(shell)
        self._mount_actions(shell)

    def _mount_label(self, shell: ctk.CTkFrame) -> None:
        ctk.CTkLabel(shell, text="Nombre", text_color=BudgetUiTheme.TXT_SEC, anchor="w").pack(anchor="w")

    def _mount_entry(self, shell: ctk.CTkFrame) -> None:
        entry = ctk.CTkEntry(
            shell,
            height=32,
            fg_color=BudgetUiTheme.BG_MAIN,
            border_color=BudgetUiTheme.BORDER,
            text_color=BudgetUiTheme.TXT_PRI,
        )
        entry.pack(fill="x", pady=(4, 12))
        entry.insert(0, self._seed)
        self._entry = entry

    def _mount_actions(self, shell: ctk.CTkFrame) -> None:
        row = ctk.CTkFrame(shell, fg_color="transparent")
        row.pack(fill="x")
        ctk.CTkButton(
            row,
            text="Cancelar",
            command=self._cancel,
            width=110,
            fg_color="transparent",
            border_width=1,
            border_color=BudgetUiTheme.BORDER,
            text_color=BudgetUiTheme.TXT_PRI,
            hover_color=BudgetUiTheme.BG_MAIN,
        ).pack(side="right")
        ctk.CTkButton(
            row,
            text="Guardar",
            command=self._confirm,
            fg_color=BudgetUiTheme.ACCENT,
            hover_color=BudgetUiTheme.ACCENT_HOVER,
            text_color="#ffffff",
            width=110,
        ).pack(side="right", padx=(0, 10))

    def _confirm(self) -> None:
        assert self._entry is not None and self._win is not None
        self._result = self._entry.get().strip()
        self._win.destroy()

    def _cancel(self) -> None:
        assert self._win is not None
        self._result = None
        self._win.destroy()
