"""Modal dialog to create or edit a single personal rule (multi-line text)."""

from __future__ import annotations

import customtkinter as ctk

from finanmind.ui.budget_ui_theme import BudgetUiTheme


class InvestmentReviewRuleEditorDialog:
    """Collects the rule body; returns the trimmed text when confirmed."""

    _WINDOW_SIZE = "520x360"

    def __init__(self, master: ctk.Misc, window_title: str, seed_text: str) -> None:
        self._master = master
        self._window_title = window_title
        self._seed = seed_text
        self._result: str | None = None
        self._win: ctk.CTkToplevel | None = None
        self._textbox: ctk.CTkTextbox | None = None

    def show(self) -> str | None:
        """Block until closed; return the text or ``None`` when cancelled."""
        self._open_window()
        assert self._win is not None
        self._master.wait_window(self._win)
        return self._result

    def _open_window(self) -> None:
        win = ctk.CTkToplevel(self._master)
        self._win = win
        win.title(self._window_title)
        win.geometry(self._WINDOW_SIZE)
        win.transient(self._master)
        win.grab_set()
        win.configure(fg_color=BudgetUiTheme.BG_CARD)
        self._build_shell(win)

    def _build_shell(self, win: ctk.CTkToplevel) -> None:
        shell = ctk.CTkFrame(win, fg_color=BudgetUiTheme.BG_CARD)
        shell.pack(fill="both", expand=True, padx=18, pady=18)
        self._mount_hint(shell)
        self._mount_textbox(shell)
        self._mount_actions(shell)

    def _mount_hint(self, shell: ctk.CTkFrame) -> None:
        text = (
            "Escribe una regla, preferencia o dato personal. La IA tendrá esto en "
            "cuenta cada vez que solicites un análisis."
        )
        ctk.CTkLabel(
            shell,
            text=text,
            text_color=BudgetUiTheme.TXT_SEC,
            font=ctk.CTkFont(size=12),
            anchor="w",
            justify="left",
            wraplength=460,
        ).pack(anchor="w", pady=(0, 8))

    def _mount_textbox(self, shell: ctk.CTkFrame) -> None:
        box = ctk.CTkTextbox(
            shell,
            fg_color=BudgetUiTheme.BG_MAIN,
            border_color=BudgetUiTheme.BORDER,
            text_color=BudgetUiTheme.TXT_PRI,
            border_width=1,
            wrap="word",
        )
        box.pack(fill="both", expand=True, pady=(0, 12))
        if self._seed:
            box.insert("1.0", self._seed)
        self._textbox = box

    def _mount_actions(self, shell: ctk.CTkFrame) -> None:
        row = ctk.CTkFrame(shell, fg_color="transparent")
        row.pack(fill="x")
        self._mount_save_button(row)
        self._mount_cancel_button(row)

    def _mount_cancel_button(self, row: ctk.CTkFrame) -> None:
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

    def _mount_save_button(self, row: ctk.CTkFrame) -> None:
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
        assert self._textbox is not None and self._win is not None
        raw = self._textbox.get("1.0", "end")
        self._result = raw.strip()
        self._win.destroy()

    def _cancel(self) -> None:
        assert self._win is not None
        self._result = None
        self._win.destroy()
