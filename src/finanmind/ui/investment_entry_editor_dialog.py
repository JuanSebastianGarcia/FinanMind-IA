"""Modal form to create or edit a single investment holding."""

from __future__ import annotations

from tkinter import messagebox

import customtkinter as ctk

from finanmind.models.investment_currency_code import InvestmentCurrencyCode
from finanmind.models.investment_entry import InvestmentEntry
from finanmind.services.cop_amount_parser import CopAmountParser
from finanmind.services.investment_service import InvestmentService
from finanmind.services.usd_amount_parser import UsdAmountParser
from finanmind.ui.budget_ui_theme import BudgetUiTheme
from finanmind.ui.iso_date_picker_row import IsoDatePickerRow


class InvestmentEntryEditorDialog:
    """Collects category, currency, amount, date, and optional description."""

    def __init__(
        self,
        master: ctk.Misc,
        service: InvestmentService,
        seed: InvestmentEntry | None,
    ) -> None:
        self._master = master
        self._service = service
        self._seed = seed
        self._win: ctk.CTkToplevel | None = None
        self._menu: ctk.CTkOptionMenu | None = None
        self._pairs: list[tuple[str, str]] = []
        self._amount: ctk.CTkEntry | None = None
        self._desc: ctk.CTkTextbox | None = None
        self._currency: ctk.CTkSegmentedButton | None = None
        self._amt_help: ctk.CTkLabel | None = None
        self._date_row = IsoDatePickerRow()

    def show(self) -> None:
        """Block until closed; mutations already persisted by the service."""
        self._spawn()
        assert self._win is not None
        self._master.wait_window(self._win)

    def _spawn(self) -> None:
        win = ctk.CTkToplevel(self._master)
        self._win = win
        win.title("Editar inversión" if self._seed else "Nueva inversión")
        win.geometry("500x560")
        win.transient(self._master)
        win.grab_set()
        win.configure(fg_color=BudgetUiTheme.BG_CARD)
        self._build(win)

    def _build(self, win: ctk.CTkToplevel) -> None:
        shell = ctk.CTkFrame(win, fg_color=BudgetUiTheme.BG_CARD)
        shell.pack(fill="both", expand=True, padx=18, pady=18)
        self._mount_category_menu(shell)
        self._mount_currency_row(shell)
        self._mount_amount_block(shell)
        self._mount_date(shell)
        self._mount_desc(shell)
        self._mount_actions(shell)

    def _mount_category_menu(self, shell: ctk.CTkFrame) -> None:
        ctk.CTkLabel(
            shell,
            text="Categoría (tu activo / bucket de inversión)",
            text_color=BudgetUiTheme.TXT_SEC,
            anchor="w",
        ).pack(anchor="w")
        self._pairs = [(c.name, c.category_id) for c in self._service.categories_snapshot()]
        labels = [p[0] for p in self._pairs] or ["Sin categorías"]
        start = self._initial_category_label(labels)
        self._menu = self._build_category_menu(shell, labels)
        self._menu.set(start)

    def _build_category_menu(self, shell: ctk.CTkFrame, labels: list[str]) -> ctk.CTkOptionMenu:
        menu = ctk.CTkOptionMenu(
            shell,
            values=labels,
            height=38,
            fg_color=BudgetUiTheme.BG_MAIN,
            button_color=BudgetUiTheme.BORDER,
            button_hover_color=BudgetUiTheme.TXT_TER,
            dropdown_fg_color=BudgetUiTheme.BG_CARD,
            dropdown_hover_color=BudgetUiTheme.BG_HOVER,
            text_color=BudgetUiTheme.TXT_PRI,
            dropdown_text_color=BudgetUiTheme.TXT_PRI,
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        menu.pack(fill="x", pady=(2, 10))
        return menu

    def _initial_category_label(self, labels: list[str]) -> str:
        if not self._pairs:
            return labels[0]
        if self._seed:
            for name, cid in self._pairs:
                if cid == self._seed.category_id:
                    return name
        return labels[0]

    def _mount_currency_row(self, shell: ctk.CTkFrame) -> None:
        ctk.CTkLabel(shell, text="Moneda del monto", text_color=BudgetUiTheme.TXT_SEC, anchor="w").pack(anchor="w")
        seed_ccy = self._seed.currency_code if self._seed else InvestmentCurrencyCode.COP
        seg = ctk.CTkSegmentedButton(
            shell,
            values=[InvestmentCurrencyCode.COP, InvestmentCurrencyCode.USD],
            command=self._on_currency_pick,
            fg_color=BudgetUiTheme.BG_MAIN,
            selected_color=BudgetUiTheme.ACCENT,
            selected_hover_color=BudgetUiTheme.ACCENT_HOVER,
        )
        seg.pack(fill="x", pady=(2, 8))
        seg.set(seed_ccy)
        self._currency = seg

    def _on_currency_pick(self, _value: str) -> None:
        self._sync_amount_help()

    def _mount_amount_block(self, shell: ctk.CTkFrame) -> None:
        self._amt_help = ctk.CTkLabel(shell, text="", text_color=BudgetUiTheme.TXT_SEC, anchor="w", font=ctk.CTkFont(size=11))
        self._amt_help.pack(anchor="w", pady=(0, 4))
        self._sync_amount_help()
        entry = ctk.CTkEntry(shell, height=32, fg_color=BudgetUiTheme.BG_MAIN, border_color=BudgetUiTheme.BORDER)
        entry.pack(fill="x", pady=(2, 6))
        if self._seed:
            self._seed_amount_into(entry, self._seed)
        self._amount = entry

    def _seed_amount_into(self, entry: ctk.CTkEntry, seed: InvestmentEntry) -> None:
        if seed.currency_code.upper() == InvestmentCurrencyCode.USD:
            entry.insert(0, f"{seed.amount:.2f}")
        else:
            entry.insert(0, str(int(round(seed.amount))))

    def _sync_amount_help(self) -> None:
        assert self._amt_help is not None and self._currency is not None
        c = self._currency.get()
        if c == InvestmentCurrencyCode.COP:
            self._amt_help.configure(text="Monto en pesos: dígitos; miles opcionales con punto.")
        else:
            self._amt_help.configure(text="Monto en dólares: use punto decimal si aplica.")

    def _mount_date(self, shell: ctk.CTkFrame) -> None:
        ctk.CTkLabel(shell, text="Fecha de inversión", text_color=BudgetUiTheme.TXT_SEC, anchor="w").pack(
            anchor="w"
        )
        seed_date = self._seed.invested_date_iso if self._seed else ""
        self._date_row.attach(shell, seed_date)

    def _mount_desc(self, shell: ctk.CTkFrame) -> None:
        ctk.CTkLabel(shell, text="Descripción (opcional)", text_color=BudgetUiTheme.TXT_SEC, anchor="w").pack(
            anchor="w"
        )
        box = ctk.CTkTextbox(shell, height=90, fg_color=BudgetUiTheme.BG_MAIN, border_color=BudgetUiTheme.BORDER)
        box.pack(fill="x", pady=(2, 10))
        if self._seed and self._seed.description:
            box.insert("1.0", self._seed.description)
        self._desc = box

    def _mount_actions(self, shell: ctk.CTkFrame) -> None:
        row = ctk.CTkFrame(shell, fg_color="transparent")
        row.pack(fill="x", pady=(6, 0))
        self._make_cancel_button(row).pack(side="right")
        self._make_save_button(row).pack(side="right", padx=(0, 10))

    def _make_cancel_button(self, row: ctk.CTkFrame) -> ctk.CTkButton:
        return ctk.CTkButton(
            row,
            text="Cancelar",
            command=self._close,
            width=110,
            fg_color="transparent",
            border_width=1,
            border_color=BudgetUiTheme.BORDER,
            text_color=BudgetUiTheme.TXT_PRI,
            hover_color=BudgetUiTheme.BG_MAIN,
        )

    def _make_save_button(self, row: ctk.CTkFrame) -> ctk.CTkButton:
        return ctk.CTkButton(
            row,
            text="Guardar",
            command=self._save,
            fg_color=BudgetUiTheme.ACCENT,
            hover_color=BudgetUiTheme.ACCENT_HOVER,
            text_color="#ffffff",
            width=110,
        )

    def _save(self) -> None:
        assert self._win is not None and self._menu is not None and self._amount is not None and self._currency is not None
        if not self._pairs:
            messagebox.showwarning("Finanmind", "Crea al menos una categoría antes de registrar inversiones.")
            return
        parsed = self._parse_amount_and_fields()
        if parsed is None:
            return
        try:
            self._persist(*parsed)
        except ValueError as exc:
            messagebox.showerror("Finanmind", str(exc))
            return
        except RuntimeError as exc:
            messagebox.showerror("Finanmind", str(exc))
            return
        self._win.destroy()

    def _parse_amount_and_fields(self) -> tuple[str, float, str, str, str] | None:
        assert self._menu is not None and self._amount is not None and self._currency is not None
        cat_id = self._selected_category_id()
        amt = self._parse_money_value()
        if amt is None:
            return None
        desc = self._read_description()
        iso = self._date_row.get_iso()
        ccy = self._currency.get()
        return cat_id, amt, iso, desc, ccy

    def _selected_category_id(self) -> str:
        assert self._menu is not None
        label = self._menu.get()
        for name, cid in self._pairs:
            if name == label:
                return cid
        return self._pairs[0][1]

    def _parse_money_value(self) -> float | None:
        assert self._amount is not None and self._currency is not None
        raw = self._amount.get()
        try:
            if self._currency.get() == InvestmentCurrencyCode.COP:
                return CopAmountParser.parse(raw)
            return UsdAmountParser.parse(raw)
        except ValueError:
            messagebox.showerror("Finanmind", "Monto inválido para la moneda seleccionada.")
            return None

    def _read_description(self) -> str:
        assert self._desc is not None
        return self._desc.get("1.0", "end").strip()

    def _persist(self, cat_id: str, amt: float, iso: str, desc: str, ccy: str) -> None:
        if self._seed:
            self._service.update_entry(self._seed.investment_id, cat_id, amt, iso, desc, ccy)
        else:
            self._service.add_entry(cat_id, amt, iso, desc, ccy)

    def _close(self) -> None:
        assert self._win is not None
        self._win.destroy()
