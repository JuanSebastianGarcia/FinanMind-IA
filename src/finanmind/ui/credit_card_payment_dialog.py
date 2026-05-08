"""Modal dialog for registering a payment against a credit card."""

from __future__ import annotations

from datetime import date
from tkinter import messagebox

import customtkinter as ctk

from finanmind.services.cop_amount_parser import CopAmountParser
from finanmind.ui.budget_ui_theme import BudgetUiTheme
from finanmind.ui.iso_date_picker_row import IsoDatePickerRow


class CreditCardPaymentDialog:
    """Collects amount, date, and notes for a card payment."""

    def __init__(self, master: ctk.Misc) -> None:
        self._master = master
        self._result: tuple[str, float, str] | None = None
        self._win: ctk.CTkToplevel | None = None
        self._date_row: IsoDatePickerRow | None = None
        self._amount_entry: ctk.CTkEntry | None = None
        self._notes_entry: ctk.CTkEntry | None = None

    def show(self) -> tuple[str, float, str] | None:
        """Return ``(paid_on, amount_cop, notes)`` when confirmed."""
        self._spawn_window()
        assert self._win is not None
        self._master.wait_window(self._win)
        return self._result

    def _spawn_window(self) -> None:
        win = ctk.CTkToplevel(self._master)
        self._win = win
        win.title("Registrar pago")
        win.geometry("520x320")
        win.transient(self._master)
        win.grab_set()
        win.configure(fg_color=BudgetUiTheme.BG_CARD)
        self._build(win)
        win.lift()
        win.focus_force()

    def _build(self, win: ctk.CTkToplevel) -> None:
        shell = ctk.CTkFrame(win, fg_color=BudgetUiTheme.BG_CARD)
        shell.pack(fill="both", expand=True, padx=18, pady=18)
        self._mount_fields(shell)
        self._mount_action_row(shell)
        self._bind_return_save(win)

    def _mount_fields(self, shell: ctk.CTkFrame) -> None:
        body = ctk.CTkFrame(shell, fg_color="transparent")
        body.pack(fill="both", expand=True)
        ctk.CTkLabel(body, text="Fecha del pago", text_color=BudgetUiTheme.TXT_SEC, anchor="w").pack(anchor="w")
        self._date_row = IsoDatePickerRow()
        self._date_row.attach(body, date.today().isoformat())
        self._mount_amount(body)
        self._mount_notes(body)

    def _mount_amount(self, body: ctk.CTkFrame) -> None:
        ctk.CTkLabel(body, text="Valor pagado (COP)", text_color=BudgetUiTheme.TXT_SEC, anchor="w").pack(anchor="w")
        entry = self._make_entry(body)
        entry.pack(fill="x", pady=(4, 10))
        self._amount_entry = entry

    def _mount_notes(self, body: ctk.CTkFrame) -> None:
        ctk.CTkLabel(body, text="Observaciones (opcional)", text_color=BudgetUiTheme.TXT_SEC, anchor="w").pack(anchor="w")
        entry = self._make_entry(body)
        entry.pack(fill="x", pady=(4, 10))
        self._notes_entry = entry

    def _make_entry(self, body: ctk.CTkFrame) -> ctk.CTkEntry:
        return ctk.CTkEntry(
            body,
            height=34,
            fg_color=BudgetUiTheme.BG_MAIN,
            border_color=BudgetUiTheme.BORDER,
            text_color=BudgetUiTheme.TXT_PRI,
        )

    def _mount_action_row(self, shell: ctk.CTkFrame) -> None:
        row = ctk.CTkFrame(shell, fg_color="transparent")
        row.pack(fill="x", side="bottom", pady=(8, 0))
        self._make_secondary(row, "Cancelar", self._cancel).pack(side="right")
        self._make_primary(row, "Guardar", self._confirm).pack(side="right", padx=(0, 10))

    def _make_primary(self, row: ctk.CTkFrame, text: str, cmd) -> ctk.CTkButton:
        return ctk.CTkButton(
            row,
            text=text,
            width=110,
            height=34,
            command=cmd,
            fg_color=BudgetUiTheme.ACCENT,
            hover_color=BudgetUiTheme.ACCENT_HOVER,
            text_color="#ffffff",
            corner_radius=8,
            font=ctk.CTkFont(size=12),
        )

    def _make_secondary(self, row: ctk.CTkFrame, text: str, cmd) -> ctk.CTkButton:
        return ctk.CTkButton(
            row,
            text=text,
            width=110,
            height=34,
            command=cmd,
            fg_color="transparent",
            border_width=1,
            border_color=BudgetUiTheme.BORDER,
            text_color=BudgetUiTheme.TXT_SEC,
            hover_color=BudgetUiTheme.BG_HOVER,
            corner_radius=8,
            font=ctk.CTkFont(size=12),
        )

    def _bind_return_save(self, win: ctk.CTkToplevel) -> None:
        win.bind("<Return>", self._on_return_save)
        if self._amount_entry is not None:
            self._amount_entry.bind("<Return>", self._on_return_save)
        if self._notes_entry is not None:
            self._notes_entry.bind("<Return>", self._on_return_save)

    def _on_return_save(self, _event: object | None = None) -> str:
        self._confirm()
        return "break"

    def _confirm(self) -> None:
        assert self._date_row and self._amount_entry and self._notes_entry
        try:
            amount = CopAmountParser.parse(self._amount_entry.get())
        except ValueError as exc:
            messagebox.showwarning("Pago", str(exc))
            return
        notes = self._notes_entry.get().strip()
        self._result = (self._date_row.get_iso(), amount, notes)
        self._shutdown()

    def _cancel(self) -> None:
        self._result = None
        self._shutdown()

    def _shutdown(self) -> None:
        if self._win is not None:
            self._win.destroy()
