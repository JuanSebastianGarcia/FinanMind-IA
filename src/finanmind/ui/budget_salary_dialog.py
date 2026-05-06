"""Modal dialog for editing monthly salary (COP)."""

from __future__ import annotations

from tkinter import messagebox

import customtkinter as ctk

from finanmind.services.cop_amount_parser import CopAmountParser


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
        self._layout_form(win)

    def _layout_form(self, win: ctk.CTkToplevel) -> None:
        frame = ctk.CTkFrame(win, fg_color="#FFFFFF")
        frame.pack(fill="both", expand=True, padx=18, pady=18)
        hint = ctk.CTkLabel(frame, text="Salario actual (COP, solo números)")
        hint.pack(anchor="w")
        seed = str(int(round(self._current_cop)))
        entry = ctk.CTkEntry(frame, height=36)
        entry.pack(fill="x", pady=(8, 14))
        entry.insert(0, seed)
        self._entry = entry
        row = ctk.CTkFrame(frame, fg_color="transparent")
        row.pack(fill="x")
        cancel = ctk.CTkButton(row, text="Cancelar", width=110, command=self._cancel)
        cancel.pack(side="right")
        confirm = ctk.CTkButton(row, text="Guardar", width=110, command=self._confirm)
        confirm.pack(side="right", padx=(0, 10))

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
