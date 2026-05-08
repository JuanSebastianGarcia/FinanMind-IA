"""Modal dialog for adding or editing a credit-card expense."""

from __future__ import annotations

from datetime import date
from tkinter import messagebox

import customtkinter as ctk

from finanmind.models.credit_card_category import CreditCardCategory
from finanmind.services.cop_amount_parser import CopAmountParser
from finanmind.ui.budget_ui_theme import BudgetUiTheme
from finanmind.ui.iso_date_picker_row import IsoDatePickerRow


class CreditCardExpenseDialog:
    """Captures amount, description, category, date, installments, and notes."""

    _SIN_CATEGORIA = "Sin categoría"

    def __init__(
        self,
        master: ctk.Misc,
        title_text: str,
        categories: list[CreditCardCategory],
        seed_amount: float,
        seed_description: str,
        seed_category_id: str,
        seed_day: str,
        seed_installments: int,
        seed_notes: str,
    ) -> None:
        self._master = master
        self._title_text = title_text
        self._categories = categories
        self._seed = (
            seed_amount,
            seed_description,
            seed_category_id,
            seed_day,
            seed_installments,
            seed_notes,
        )
        self._result: tuple[float, str, str, str, int, str] | None = None
        self._win: ctk.CTkToplevel | None = None
        self._caption_to_id = self._build_caption_map(categories)
        self._category_var = ctk.StringVar(value=self._initial_caption(seed_category_id))
        self._amount_entry: ctk.CTkEntry | None = None
        self._description_entry: ctk.CTkEntry | None = None
        self._installments_entry: ctk.CTkEntry | None = None
        self._notes_entry: ctk.CTkEntry | None = None
        self._date_row: IsoDatePickerRow | None = None

    def show(self) -> tuple[float, str, str, str, int, str] | None:
        """Return ``(amount, description, category_id, day, installments, notes)``."""
        self._spawn_window()
        assert self._win is not None
        self._master.wait_window(self._win)
        return self._result

    def _build_caption_map(self, categories: list[CreditCardCategory]) -> dict[str, str]:
        out = {self._SIN_CATEGORIA: ""}
        for cat in categories:
            out[cat.title] = cat.category_id
        return out

    def _initial_caption(self, category_id: str) -> str:
        for caption, cid in self._caption_to_id.items():
            if cid == category_id:
                return caption
        return self._SIN_CATEGORIA

    def _spawn_window(self) -> None:
        win = ctk.CTkToplevel(self._master)
        self._win = win
        win.title(self._title_text)
        win.geometry("560x520")
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
        self._mount_amount(body)
        self._mount_description(body)
        self._mount_category(body)
        self._mount_date(body)
        self._mount_installments_and_notes(body)

    def _mount_amount(self, body: ctk.CTkFrame) -> None:
        ctk.CTkLabel(body, text="Valor (COP)", text_color=BudgetUiTheme.TXT_SEC, anchor="w").pack(anchor="w")
        entry = self._make_entry(body)
        entry.pack(fill="x", pady=(4, 10))
        if self._seed[0] > 0:
            entry.insert(0, str(int(round(self._seed[0]))))
        self._amount_entry = entry

    def _mount_description(self, body: ctk.CTkFrame) -> None:
        ctk.CTkLabel(body, text="Descripción", text_color=BudgetUiTheme.TXT_SEC, anchor="w").pack(anchor="w")
        entry = self._make_entry(body)
        entry.pack(fill="x", pady=(4, 10))
        entry.insert(0, self._seed[1])
        self._description_entry = entry

    def _mount_category(self, body: ctk.CTkFrame) -> None:
        ctk.CTkLabel(body, text="Categoría", text_color=BudgetUiTheme.TXT_SEC, anchor="w").pack(anchor="w")
        captions = list(self._caption_to_id.keys())
        menu = ctk.CTkOptionMenu(
            body,
            variable=self._category_var,
            values=captions or [self._SIN_CATEGORIA],
            fg_color=BudgetUiTheme.BG_MAIN,
            button_color=BudgetUiTheme.BORDER,
            button_hover_color=BudgetUiTheme.TXT_TER,
            dropdown_fg_color=BudgetUiTheme.BG_CARD,
            dropdown_text_color=BudgetUiTheme.TXT_PRI,
            text_color=BudgetUiTheme.TXT_PRI,
            height=34,
        )
        menu.pack(fill="x", pady=(4, 10))

    def _mount_date(self, body: ctk.CTkFrame) -> None:
        ctk.CTkLabel(body, text="Fecha del gasto", text_color=BudgetUiTheme.TXT_SEC, anchor="w").pack(anchor="w")
        seed_day = self._seed[3] if self._seed[3] else date.today().isoformat()
        self._date_row = IsoDatePickerRow()
        self._date_row.attach(body, seed_day)

    def _mount_installments_and_notes(self, body: ctk.CTkFrame) -> None:
        self._mount_installments(body)
        self._mount_notes(body)

    def _mount_installments(self, body: ctk.CTkFrame) -> None:
        ctk.CTkLabel(body, text="Cuotas (1 = pago único)", text_color=BudgetUiTheme.TXT_SEC, anchor="w").pack(anchor="w")
        entry = self._make_entry(body)
        entry.pack(fill="x", pady=(4, 10))
        seed_inst = max(int(self._seed[4] or 1), 1)
        entry.insert(0, str(seed_inst))
        self._installments_entry = entry

    def _mount_notes(self, body: ctk.CTkFrame) -> None:
        ctk.CTkLabel(body, text="Observaciones (opcional)", text_color=BudgetUiTheme.TXT_SEC, anchor="w").pack(anchor="w")
        entry = self._make_entry(body)
        entry.pack(fill="x", pady=(4, 10))
        entry.insert(0, self._seed[5])
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
        for entry in (
            self._amount_entry,
            self._description_entry,
            self._installments_entry,
            self._notes_entry,
        ):
            if entry is not None:
                entry.bind("<Return>", self._on_return_save)

    def _on_return_save(self, _event: object | None = None) -> str:
        self._confirm()
        return "break"

    def _confirm(self) -> None:
        try:
            payload = self._collect_payload()
        except ValueError as exc:
            messagebox.showwarning("Gasto", str(exc))
            return
        self._result = payload
        self._shutdown()

    def _collect_payload(self) -> tuple[float, str, str, str, int, str]:
        assert self._amount_entry and self._description_entry and self._date_row
        assert self._installments_entry and self._notes_entry
        amount = CopAmountParser.parse(self._amount_entry.get())
        description = self._description_entry.get().strip()
        if description == "":
            raise ValueError("La descripción es obligatoria.")
        category_id = self._caption_to_id.get(self._category_var.get(), "")
        installments = self._parse_installments(self._installments_entry.get())
        notes = self._notes_entry.get().strip()
        return amount, description, category_id, self._date_row.get_iso(), installments, notes

    def _parse_installments(self, raw: str) -> int:
        try:
            value = int(raw.strip() or "1")
        except ValueError as exc:
            raise ValueError("Las cuotas deben ser un entero.") from exc
        if value < 1:
            raise ValueError("Las cuotas deben ser ≥ 1.")
        return value

    def _cancel(self) -> None:
        self._result = None
        self._shutdown()

    def _shutdown(self) -> None:
        if self._win is not None:
            self._win.destroy()
