"""Modal dialog for editing monthly salary (COP)."""

from __future__ import annotations

from tkinter import messagebox

import customtkinter as ctk

from finanmind.services.cop_amount_parser import CopAmountParser
from finanmind.ui.budget_ui_theme import BudgetUiTheme


class BudgetSalaryDialog:
    """Captures a single COP salary figure."""

    def __init__(self, master: ctk.Misc, current_cop: float) -> None:
        self._master = master
        self._current_cop = current_cop
        self._result: float | None = None
        self._win: ctk.CTkToplevel | None = None
        self._entry: ctk.CTkEntry | None = None

    def show(self) -> float | None:
        """Block until the dialog closes; return COP amount or ``None``."""
        self._open_window()
        assert self._win is not None
        self._master.wait_window(self._win)
        return self._result

    def _open_window(self) -> None:
        win = ctk.CTkToplevel(self._master)
        self._win = win
        win.title("Salario mensual")
        win.geometry("420x200")
        win.transient(self._master)
        win.grab_set()
        win.configure(fg_color=BudgetUiTheme.BG_CARD)
        self._layout_form(win)

    def _layout_form(self, win: ctk.CTkToplevel) -> None:
        frame = ctk.CTkFrame(win, fg_color=BudgetUiTheme.BG_CARD)
        frame.pack(fill="both", expand=True, padx=18, pady=18)
        hint = ctk.CTkLabel(
            frame,
            text="Salario actual (COP, solo números)",
            text_color=BudgetUiTheme.TXT_SEC,
            anchor="w",
        )
        hint.pack(anchor="w")
        seed = str(int(round(self._current_cop)))
        entry = ctk.CTkEntry(
            frame,
            height=36,
            fg_color=BudgetUiTheme.BG_MAIN,
            border_color=BudgetUiTheme.BORDER,
            text_color=BudgetUiTheme.TXT_PRI,
        )
        entry.pack(fill="x", pady=(8, 14))
        entry.insert(0, seed)
        self._entry = entry
        row = ctk.CTkFrame(frame, fg_color="transparent")
        row.pack(fill="x")
        self._outline_dialog_btn(row, "Cancelar", self._cancel).pack(side="right")
        self._accent_dialog_btn(row, "Guardar", self._confirm).pack(side="right", padx=(0, 10))

    def _accent_dialog_btn(self, row: ctk.CTkFrame, text: str, cmd) -> ctk.CTkButton:
        return ctk.CTkButton(
            row,
            text=text,
            width=110,
            height=32,
            command=cmd,
            fg_color=BudgetUiTheme.ACCENT,
            hover_color=BudgetUiTheme.ACCENT_HOVER,
            text_color="#ffffff",
            corner_radius=8,
            font=ctk.CTkFont(size=12),
        )

    def _outline_dialog_btn(self, row: ctk.CTkFrame, text: str, cmd) -> ctk.CTkButton:
        return ctk.CTkButton(
            row,
            text=text,
            width=110,
            height=32,
            command=cmd,
            fg_color="transparent",
            border_width=1,
            border_color=BudgetUiTheme.BORDER,
            text_color=BudgetUiTheme.TXT_SEC,
            hover_color=BudgetUiTheme.BG_HOVER,
            corner_radius=8,
            font=ctk.CTkFont(size=12),
        )

    def _confirm(self) -> None:
        assert self._entry is not None
        try:
            parsed = CopAmountParser.parse(self._entry.get())
        except ValueError as exc:
            messagebox.showwarning("Salario", str(exc))
            return
        self._result = parsed
        self._close()

    def _cancel(self) -> None:
        self._result = None
        self._close()

    def _close(self) -> None:
        if self._win is not None:
            self._win.destroy()
