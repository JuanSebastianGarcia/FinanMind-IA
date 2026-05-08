"""Modal dialog for adding or editing a credit card."""

from __future__ import annotations

from tkinter import messagebox

import customtkinter as ctk

from finanmind.budget.palette import BudgetCategoryPalette
from finanmind.services.cop_amount_parser import CopAmountParser
from finanmind.ui.budget_ui_theme import BudgetUiTheme


class CreditCardDialog:
    """Collects card alias, total limit, cycle days, and palette color."""

    def __init__(
        self,
        master: ctk.Misc,
        title_text: str,
        seed_name: str,
        seed_limit: float,
        seed_cut_day: int,
        seed_due_day: int,
        seed_color: str,
    ) -> None:
        self._master = master
        self._title_text = title_text
        self._seed_name = seed_name
        self._seed_limit = seed_limit
        self._seed_cut_day = seed_cut_day
        self._seed_due_day = seed_due_day
        self._seed_color = seed_color
        self._result: tuple[str, float, int, int, str] | None = None
        self._win: ctk.CTkToplevel | None = None
        self._name_entry: ctk.CTkEntry | None = None
        self._limit_entry: ctk.CTkEntry | None = None
        self._cut_entry: ctk.CTkEntry | None = None
        self._due_entry: ctk.CTkEntry | None = None
        self._color_var = ctk.StringVar(value=seed_color or BudgetCategoryPalette.PRESETS[0])

    def show(self) -> tuple[str, float, int, int, str] | None:
        """Return ``(name, limit, cut_day, payment_due_day, color)`` when confirmed."""
        self._spawn_window()
        assert self._win is not None
        self._master.wait_window(self._win)
        return self._result

    def _spawn_window(self) -> None:
        win = ctk.CTkToplevel(self._master)
        self._win = win
        win.title(self._title_text)
        win.geometry("520x440")
        win.transient(self._master)
        win.grab_set()
        win.configure(fg_color=BudgetUiTheme.BG_CARD)
        self._build(win)

    def _build(self, win: ctk.CTkToplevel) -> None:
        shell = ctk.CTkFrame(win, fg_color=BudgetUiTheme.BG_CARD)
        shell.pack(fill="both", expand=True, padx=18, pady=18)
        self._mount_name_field(shell)
        self._mount_limit_field(shell)
        self._mount_days_row(shell)
        self._mount_color_row(shell)
        self._mount_action_row(shell)
        self._bind_return_saves()

    def _mount_name_field(self, shell: ctk.CTkFrame) -> None:
        ctk.CTkLabel(shell, text="Alias de la tarjeta", text_color=BudgetUiTheme.TXT_SEC, anchor="w").pack(anchor="w")
        entry = self._make_entry(shell)
        entry.pack(fill="x", pady=(4, 10))
        entry.insert(0, self._seed_name)
        self._name_entry = entry

    def _mount_limit_field(self, shell: ctk.CTkFrame) -> None:
        ctk.CTkLabel(shell, text="Cupo total (COP)", text_color=BudgetUiTheme.TXT_SEC, anchor="w").pack(anchor="w")
        entry = self._make_entry(shell)
        entry.pack(fill="x", pady=(4, 10))
        if self._seed_limit > 0:
            entry.insert(0, str(int(round(self._seed_limit))))
        self._limit_entry = entry

    def _mount_days_row(self, shell: ctk.CTkFrame) -> None:
        row = ctk.CTkFrame(shell, fg_color="transparent")
        row.pack(fill="x", pady=(0, 10))
        self._mount_day_field(row, "Día de corte", "_cut_entry", self._seed_cut_day)
        self._mount_day_field(row, "Día de pago", "_due_entry", self._seed_due_day)

    def _mount_day_field(self, row: ctk.CTkFrame, caption: str, attr: str, seed: int) -> None:
        col = ctk.CTkFrame(row, fg_color="transparent")
        col.pack(side="left", expand=True, fill="x", padx=(0, 10))
        ctk.CTkLabel(col, text=caption, text_color=BudgetUiTheme.TXT_SEC, anchor="w").pack(anchor="w")
        entry = self._make_entry(col)
        entry.pack(fill="x", pady=(4, 0))
        entry.insert(0, str(int(seed)) if seed else "")
        setattr(self, attr, entry)

    def _mount_color_row(self, shell: ctk.CTkFrame) -> None:
        ctk.CTkLabel(shell, text="Color", text_color=BudgetUiTheme.TXT_SEC, anchor="w").pack(anchor="w")
        wrap = ctk.CTkFrame(shell, fg_color="transparent")
        wrap.pack(fill="x", pady=(4, 12))
        for color in BudgetCategoryPalette.PRESETS:
            self._mount_color_chip(wrap, color)

    def _mount_color_chip(self, wrap: ctk.CTkFrame, color: str) -> None:
        chip = ctk.CTkButton(
            wrap,
            text=" ",
            width=22,
            height=22,
            corner_radius=12,
            fg_color=color,
            hover_color=color,
            border_color=BudgetUiTheme.BORDER,
            border_width=1,
            command=lambda c=color: self._color_var.set(c),
        )
        chip.pack(side="left", padx=2)

    def _mount_action_row(self, shell: ctk.CTkFrame) -> None:
        row = ctk.CTkFrame(shell, fg_color="transparent")
        row.pack(fill="x", pady=(8, 0))
        self._make_secondary(row, "Cancelar", self._cancel).pack(side="right")
        self._make_primary(row, "Guardar", self._confirm).pack(side="right", padx=(0, 10))

    def _make_entry(self, parent: ctk.CTkBaseClass) -> ctk.CTkEntry:
        return ctk.CTkEntry(
            parent,
            height=32,
            fg_color=BudgetUiTheme.BG_MAIN,
            border_color=BudgetUiTheme.BORDER,
            text_color=BudgetUiTheme.TXT_PRI,
        )

    def _make_primary(self, row: ctk.CTkFrame, text: str, cmd) -> ctk.CTkButton:
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

    def _make_secondary(self, row: ctk.CTkFrame, text: str, cmd) -> ctk.CTkButton:
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

    def _bind_return_saves(self) -> None:
        for entry in (self._name_entry, self._limit_entry, self._cut_entry, self._due_entry):
            assert entry is not None
            entry.bind("<Return>", self._on_return_save)

    def _on_return_save(self, _event: object) -> None:
        self._confirm()

    def _confirm(self) -> None:
        try:
            payload = self._collect_payload()
        except ValueError as exc:
            messagebox.showwarning("Tarjeta", str(exc))
            return
        self._result = payload
        self._shutdown()

    def _collect_payload(self) -> tuple[str, float, int, int, str]:
        assert self._name_entry and self._limit_entry and self._cut_entry and self._due_entry
        name = self._name_entry.get().strip()
        if name == "":
            raise ValueError("El alias es obligatorio.")
        limit = CopAmountParser.parse(self._limit_entry.get())
        cut_day = self._parse_day(self._cut_entry.get(), "corte")
        due_day = self._parse_day(self._due_entry.get(), "pago")
        return (name, limit, cut_day, due_day, self._color_var.get())

    def _parse_day(self, raw: str, label: str) -> int:
        try:
            value = int(raw.strip())
        except ValueError as exc:
            raise ValueError(f"Día de {label} inválido.") from exc
        if not 1 <= value <= 31:
            raise ValueError(f"Día de {label} debe estar entre 1 y 31.")
        return value

    def _cancel(self) -> None:
        self._result = None
        self._shutdown()

    def _shutdown(self) -> None:
        if self._win is not None:
            self._win.destroy()
