"""Modal dialog for allocating part of a receipt to a budget label."""

from __future__ import annotations

from datetime import date

from tkinter import messagebox

import customtkinter as ctk

from finanmind.models.budget_category import BudgetCategory
from finanmind.models.budget_workspace import BudgetWorkspace
from finanmind.services.cop_amount_parser import CopAmountParser
from finanmind.ui.iso_date_picker_row import IsoDatePickerRow


class DistributionLineDialog:
    """Collects allocation date, label, COP amount, and memo."""

    def __init__(
        self,
        master: ctk.Misc,
        workspace: BudgetWorkspace,
        default_day: str,
    ) -> None:
        self._master = master
        self._workspace = workspace
        self._default_day = default_day
        self._pairs = self._flatten_labels(workspace)
        self._result: tuple[str, str, float, str] | None = None
        self._win: ctk.CTkToplevel | None = None
        self._menu: ctk.CTkOptionMenu | None = None
        self._date_row: IsoDatePickerRow | None = None
        self._amount_entry: ctk.CTkEntry | None = None
        self._memo_entry: ctk.CTkEntry | None = None

    def show(self) -> tuple[str, str, float, str] | None:
        """Return ``(occurred_on, label_id, amount_cop, memo)`` when confirmed."""
        if not self._pairs:
            messagebox.showinfo(
                "Distribución",
                "No hay etiquetas en el presupuesto. Configura etiquetas primero.",
            )
            return None
        self._spawn_window()
        assert self._win is not None
        self._master.wait_window(self._win)
        return self._result

    def _spawn_window(self) -> None:
        win = ctk.CTkToplevel(self._master)
        self._win = win
        win.title("Registrar distribución")
        win.geometry("600x480")
        win.minsize(560, 420)
        win.transient(self._master.winfo_toplevel())
        win.grab_set()
        self._build(win)

    def _build(self, win: ctk.CTkToplevel) -> None:
        shell = ctk.CTkFrame(win, fg_color="#FFFFFF")
        shell.pack(fill="both", expand=True, padx=20, pady=20)
        self._mount_footer(shell)
        self._mount_fields(shell)

    def _mount_footer(self, shell: ctk.CTkFrame) -> None:
        row = ctk.CTkFrame(shell, fg_color="transparent")
        row.pack(fill="x", side="bottom", pady=(16, 0))
        ctk.CTkButton(row, text="Cancelar", width=120, height=36, command=self._cancel).pack(side="right")
        ctk.CTkButton(row, text="Guardar", width=120, height=36, command=self._confirm).pack(side="right", padx=(0, 12))

    def _mount_fields(self, shell: ctk.CTkFrame) -> None:
        body = ctk.CTkFrame(shell, fg_color="transparent")
        body.pack(fill="both", expand=True)
        self._mount_label_choice(body)
        self._mount_date_choice(body)
        self._mount_amount_inputs(body)

    def _mount_label_choice(self, body: ctk.CTkFrame) -> None:
        ctk.CTkLabel(body, text="Etiqueta").pack(anchor="w")
        captions = [cap for cap, _ in self._pairs]
        menu = ctk.CTkOptionMenu(body, values=captions, height=36)
        menu.pack(fill="x", pady=(4, 12))
        menu.set(captions[0])
        self._menu = menu

    def _mount_date_choice(self, body: ctk.CTkFrame) -> None:
        ctk.CTkLabel(body, text="Fecha").pack(anchor="w")
        seed = self._default_day if self._default_day else date.today().isoformat()
        self._date_row = IsoDatePickerRow(body)
        self._date_row.attach(body, seed)

    def _mount_amount_inputs(self, body: ctk.CTkFrame) -> None:
        ctk.CTkLabel(body, text="Importe COP").pack(anchor="w")
        amount_entry = ctk.CTkEntry(body, height=36)
        amount_entry.pack(fill="x", pady=(4, 12))
        self._amount_entry = amount_entry
        ctk.CTkLabel(body, text="Nota (opcional)").pack(anchor="w")
        memo_entry = ctk.CTkEntry(body, height=36)
        memo_entry.pack(fill="x", pady=(4, 12))
        self._memo_entry = memo_entry

    def _confirm(self) -> None:
        payload = self._read_payload()
        if payload is None:
            return
        self._result = payload
        self._shutdown()

    def _read_payload(self) -> tuple[str, str, float, str] | None:
        assert self._menu and self._date_row and self._amount_entry and self._memo_entry
        caption = self._menu.get()
        label_id = self._label_id_for_caption(caption)
        if label_id is None:
            messagebox.showwarning("Distribución", "Selecciona una etiqueta válida.")
            return None
        day = self._date_row.get_iso()
        try:
            amount = CopAmountParser.parse(self._amount_entry.get())
        except ValueError as exc:
            messagebox.showwarning("Distribución", str(exc))
            return None
        memo = self._memo_entry.get().strip()
        return (day, label_id, amount, memo)

    def _cancel(self) -> None:
        self._result = None
        self._shutdown()

    def _shutdown(self) -> None:
        if self._win is not None:
            self._win.destroy()

    def _label_id_for_caption(self, caption: str) -> str | None:
        for cap, lid in self._pairs:
            if cap == caption:
                return lid
        return None

    def _flatten_labels(self, workspace: BudgetWorkspace) -> list[tuple[str, str]]:
        pairs: list[tuple[str, str]] = []
        for cat in workspace.categories:
            cat_prefix = self._category_prefix(cat)
            for lbl in cat.labels:
                pairs.append((f"{cat_prefix}{lbl.title}", lbl.label_id))
        return pairs

    def _category_prefix(self, cat: BudgetCategory) -> str:
        title = cat.title.strip()
        if title == "":
            return ""
        return f"{title} · "
