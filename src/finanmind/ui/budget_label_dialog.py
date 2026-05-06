"""Modal dialog for adding or editing labels."""

from __future__ import annotations

from tkinter import messagebox

import customtkinter as ctk

from finanmind.services.cop_amount_parser import CopAmountParser


class BudgetLabelDialog:
    """Collects label title plus COP amount."""

    def __init__(self, master: ctk.Misc, title: str, amount_cop: float) -> None:
        self._master = master
        self._seed_title = title
        self._seed_amount = amount_cop
        self._result: tuple[str, float] | None = None
        self._win: ctk.CTkToplevel | None = None
        self._title_entry: ctk.CTkEntry | None = None
        self._amount_entry: ctk.CTkEntry | None = None

    def show(self) -> tuple[str, float] | None:
        """Return ``(title, amount_cop)`` when confirmed."""
        self._spawn_window()
        assert self._win is not None
        self._master.wait_window(self._win)
        return self._result

    def _spawn_window(self) -> None:
        win = ctk.CTkToplevel(self._master)
        self._win = win
        win.title("Etiqueta")
        win.geometry("460x220")
        win.transient(self._master)
        win.grab_set()
        self._build(win)

    def _build(self, win: ctk.CTkToplevel) -> None:
        shell = ctk.CTkFrame(win, fg_color="#FFFFFF")
        shell.pack(fill="both", expand=True, padx=18, pady=18)
        ctk.CTkLabel(shell, text="Nombre").pack(anchor="w")
        title_entry = ctk.CTkEntry(shell, height=32)
        title_entry.pack(fill="x", pady=(4, 10))
        title_entry.insert(0, self._seed_title)
        self._title_entry = title_entry
        ctk.CTkLabel(shell, text="Importe COP").pack(anchor="w")
        amount_entry = ctk.CTkEntry(shell, height=32)
        amount_entry.pack(fill="x", pady=(4, 10))
        amount_entry.insert(0, str(int(round(self._seed_amount))))
        self._amount_entry = amount_entry
        row = ctk.CTkFrame(shell, fg_color="transparent")
        row.pack(fill="x", pady=(6, 0))
        ctk.CTkButton(row, text="Cancelar", width=110, command=self._cancel).pack(side="right")
        ctk.CTkButton(row, text="Guardar", width=110, command=self._confirm).pack(side="right", padx=(0, 10))

    def _confirm(self) -> None:
        assert self._title_entry and self._amount_entry
        title = self._title_entry.get().strip()
        if title == "":
            messagebox.showwarning("Etiqueta", "El nombre es obligatorio.")
            return
        try:
            amount = CopAmountParser.parse(self._amount_entry.get())
        except ValueError as exc:
            messagebox.showwarning("Etiqueta", str(exc))
            return
        self._result = (title, amount)
        self._shutdown()

    def _cancel(self) -> None:
        self._result = None
        self._shutdown()

    def _shutdown(self) -> None:
        if self._win is not None:
            self._win.destroy()
