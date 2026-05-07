"""Modal dialog for registering a payroll receipt."""

from __future__ import annotations

from datetime import date

from tkinter import messagebox

import customtkinter as ctk

from finanmind.services.cop_amount_parser import CopAmountParser
from finanmind.ui.budget_ui_theme import BudgetUiTheme
from finanmind.ui.iso_date_picker_row import IsoDatePickerRow


class DistributionReceiptDialog:
    """Collects receipt date, COP amount, and memo."""

    def __init__(self, master: ctk.Misc) -> None:
        self._master = master
        self._result: tuple[str, float, str] | None = None
        self._win: ctk.CTkToplevel | None = None
        self._date_row: IsoDatePickerRow | None = None
        self._amount_entry: ctk.CTkEntry | None = None
        self._memo_entry: ctk.CTkEntry | None = None

    def show(self) -> tuple[str, float, str] | None:
        """Return ``(occurred_on, amount_cop, memo)`` when confirmed."""
        self._spawn_window()
        assert self._win is not None
        self._master.wait_window(self._win)
        return self._result

    def _spawn_window(self) -> None:
        win = ctk.CTkToplevel(self._master)
        self._win = win
        win.title("Nuevo ingreso")
        win.geometry("560x420")
        win.minsize(520, 380)
        win.configure(fg_color=BudgetUiTheme.BG_CARD)
        win.transient(self._master)
        win.grab_set()
        self._build(win)
        self._wire_enter_save(win)
        win.lift()
        win.focus_force()

    def _build(self, win: ctk.CTkToplevel) -> None:
        shell = ctk.CTkFrame(win, fg_color=BudgetUiTheme.BG_CARD)
        shell.pack(fill="both", expand=True, padx=20, pady=20)
        self._mount_fields(shell)
        self._mount_footer(shell)

    def _mount_footer(self, shell: ctk.CTkFrame) -> None:
        row = ctk.CTkFrame(shell, fg_color="transparent")
        row.pack(fill="x", side="bottom", pady=(16, 0))
        self._secondary_btn(row, "Cancelar", self._cancel).pack(side="right")
        self._primary_btn(row, "Guardar", self._confirm).pack(side="right", padx=(0, 12))

    def _primary_btn(self, row: ctk.CTkFrame, text: str, cmd) -> ctk.CTkButton:
        return ctk.CTkButton(
            row,
            text=text,
            width=120,
            height=36,
            command=cmd,
            fg_color=BudgetUiTheme.ACCENT,
            hover_color=BudgetUiTheme.ACCENT_HOVER,
            text_color="#ffffff",
            corner_radius=8,
            font=ctk.CTkFont(size=13),
        )

    def _secondary_btn(self, row: ctk.CTkFrame, text: str, cmd) -> ctk.CTkButton:
        return ctk.CTkButton(
            row,
            text=text,
            width=120,
            height=36,
            command=cmd,
            fg_color="transparent",
            border_width=1,
            border_color=BudgetUiTheme.BORDER,
            text_color=BudgetUiTheme.TXT_SEC,
            hover_color=BudgetUiTheme.BG_HOVER,
            corner_radius=8,
            font=ctk.CTkFont(size=13),
        )

    def _mount_fields(self, shell: ctk.CTkFrame) -> None:
        body = ctk.CTkFrame(shell, fg_color="transparent")
        body.pack(fill="both", expand=True)
        ctk.CTkLabel(body, text="Fecha", text_color=BudgetUiTheme.TXT_SEC, anchor="w").pack(anchor="w")
        self._date_row = IsoDatePickerRow()
        self._date_row.attach(body, date.today().isoformat())
        ctk.CTkLabel(body, text="Importe COP", text_color=BudgetUiTheme.TXT_SEC, anchor="w").pack(anchor="w")
        amount_entry = self._styled_entry(body)
        amount_entry.pack(fill="x", pady=(4, 12))
        self._amount_entry = amount_entry
        ctk.CTkLabel(body, text="Descripción (opcional)", text_color=BudgetUiTheme.TXT_SEC, anchor="w").pack(anchor="w")
        memo_entry = self._styled_entry(body)
        memo_entry.pack(fill="x", pady=(4, 12))
        self._memo_entry = memo_entry

    def _wire_enter_save(self, win: ctk.CTkToplevel) -> None:
        win.bind("<Return>", self._enter_save)
        assert self._amount_entry and self._memo_entry
        self._amount_entry.bind("<Return>", self._enter_save)
        self._memo_entry.bind("<Return>", self._enter_save)

    def _enter_save(self, _event: object | None = None) -> str:
        self._confirm()
        return "break"

    def _styled_entry(self, body: ctk.CTkFrame) -> ctk.CTkEntry:
        return ctk.CTkEntry(
            body,
            height=36,
            fg_color=BudgetUiTheme.BG_MAIN,
            border_color=BudgetUiTheme.BORDER,
            text_color=BudgetUiTheme.TXT_PRI,
        )

    def _confirm(self) -> None:
        assert self._date_row and self._amount_entry and self._memo_entry
        day = self._date_row.get_iso()
        try:
            amount = CopAmountParser.parse(self._amount_entry.get())
        except ValueError as exc:
            messagebox.showwarning("Ingreso", str(exc))
            return
        memo = self._memo_entry.get().strip()
        self._result = (day, amount, memo)
        self._shutdown()

    def _cancel(self) -> None:
        self._result = None
        self._shutdown()

    def _shutdown(self) -> None:
        if self._win is not None:
            self._win.destroy()
