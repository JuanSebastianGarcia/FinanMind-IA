"""Modal dialog for adding or editing labels."""

from __future__ import annotations

from tkinter import messagebox

import customtkinter as ctk

from finanmind.services.cop_amount_parser import CopAmountParser
from finanmind.ui.budget_ui_theme import BudgetUiTheme


class BudgetLabelDialog:
    """Collects label title, COP amount, and an optional credit-card link."""

    _NO_LINK_CAPTION = "Sin enlace"

    def __init__(
        self,
        master: ctk.Misc,
        title: str,
        amount_cop: float,
        *,
        link_options: list[tuple[str, str]] | None = None,
        seed_link_id: str = "",
    ) -> None:
        self._master = master
        self._seed_title = title
        self._seed_amount = amount_cop
        self._result: tuple[str, float, str] | None = None
        self._win: ctk.CTkToplevel | None = None
        self._title_entry: ctk.CTkEntry | None = None
        self._amount_entry: ctk.CTkEntry | None = None
        self._link_options = list(link_options or [])
        self._caption_to_cc_id = self._build_link_map(self._link_options)
        self._link_var = ctk.StringVar(value=self._initial_link_caption(seed_link_id))

    def show(self) -> tuple[str, float, str] | None:
        """Return ``(title, amount_cop, linked_cc_category_id)`` when confirmed."""
        self._spawn_window()
        assert self._win is not None
        self._master.wait_window(self._win)
        return self._result

    def _build_link_map(self, options: list[tuple[str, str]]) -> dict[str, str]:
        out = {self._NO_LINK_CAPTION: ""}
        for caption, cc_id in options:
            out[caption] = cc_id
        return out

    def _initial_link_caption(self, seed_link_id: str) -> str:
        token = seed_link_id.strip()
        for caption, cc_id in self._caption_to_cc_id.items():
            if cc_id == token and token != "":
                return caption
        return self._NO_LINK_CAPTION

    def _spawn_window(self) -> None:
        win = ctk.CTkToplevel(self._master)
        self._win = win
        win.title("Etiqueta")
        win.geometry("480x300" if self._link_options else "460x220")
        win.transient(self._master)
        win.grab_set()
        win.configure(fg_color=BudgetUiTheme.BG_CARD)
        self._build(win)

    def _build(self, win: ctk.CTkToplevel) -> None:
        shell = ctk.CTkFrame(win, fg_color=BudgetUiTheme.BG_CARD)
        shell.pack(fill="both", expand=True, padx=18, pady=18)
        self._mount_name_field(shell)
        self._mount_amount_field(shell)
        if self._link_options:
            self._mount_link_row(shell)
        self._mount_action_row(shell)
        self._bind_return_saves()

    def _mount_name_field(self, shell: ctk.CTkFrame) -> None:
        ctk.CTkLabel(shell, text="Nombre", text_color=BudgetUiTheme.TXT_SEC, anchor="w").pack(anchor="w")
        title_entry = ctk.CTkEntry(
            shell,
            height=32,
            fg_color=BudgetUiTheme.BG_MAIN,
            border_color=BudgetUiTheme.BORDER,
            text_color=BudgetUiTheme.TXT_PRI,
        )
        title_entry.pack(fill="x", pady=(4, 10))
        title_entry.insert(0, self._seed_title)
        self._title_entry = title_entry

    def _mount_amount_field(self, shell: ctk.CTkFrame) -> None:
        ctk.CTkLabel(shell, text="Importe COP", text_color=BudgetUiTheme.TXT_SEC, anchor="w").pack(anchor="w")
        amount_entry = ctk.CTkEntry(
            shell,
            height=32,
            fg_color=BudgetUiTheme.BG_MAIN,
            border_color=BudgetUiTheme.BORDER,
            text_color=BudgetUiTheme.TXT_PRI,
        )
        amount_entry.pack(fill="x", pady=(4, 10))
        amount_entry.insert(0, str(int(round(self._seed_amount))))
        self._amount_entry = amount_entry

    def _mount_link_row(self, shell: ctk.CTkFrame) -> None:
        self._mount_link_caption(shell)
        self._mount_link_menu(shell)

    def _mount_link_caption(self, shell: ctk.CTkFrame) -> None:
        ctk.CTkLabel(
            shell,
            text="Vincular a tarjeta · categoría",
            text_color=BudgetUiTheme.TXT_SEC,
            anchor="w",
        ).pack(anchor="w")

    def _mount_link_menu(self, shell: ctk.CTkFrame) -> None:
        ctk.CTkOptionMenu(
            shell,
            variable=self._link_var,
            values=list(self._caption_to_cc_id.keys()),
            fg_color=BudgetUiTheme.BG_MAIN,
            button_color=BudgetUiTheme.BORDER,
            button_hover_color=BudgetUiTheme.TXT_TER,
            dropdown_fg_color=BudgetUiTheme.BG_CARD,
            dropdown_text_color=BudgetUiTheme.TXT_PRI,
            text_color=BudgetUiTheme.TXT_PRI,
            height=32,
        ).pack(fill="x", pady=(4, 10))

    def _mount_action_row(self, shell: ctk.CTkFrame) -> None:
        row = ctk.CTkFrame(shell, fg_color="transparent")
        row.pack(fill="x", pady=(6, 0))
        self._mount_secondary_btn(row, "Cancelar", self._cancel).pack(side="right")
        self._mount_primary_btn(row, "Guardar", self._confirm).pack(side="right", padx=(0, 10))

    def _mount_primary_btn(self, row: ctk.CTkFrame, text: str, cmd) -> ctk.CTkButton:
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

    def _mount_secondary_btn(self, row: ctk.CTkFrame, text: str, cmd) -> ctk.CTkButton:
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
        assert self._title_entry and self._amount_entry
        self._title_entry.bind("<Return>", self._on_return_save)
        self._amount_entry.bind("<Return>", self._on_return_save)

    def _on_return_save(self, _event: object) -> None:
        self._confirm()

    def _confirm(self) -> None:
        try:
            payload = self._collect_payload()
        except ValueError as exc:
            messagebox.showwarning("Etiqueta", str(exc))
            return
        self._result = payload
        self._shutdown()

    def _collect_payload(self) -> tuple[str, float, str]:
        assert self._title_entry and self._amount_entry
        title = self._title_entry.get().strip()
        if title == "":
            raise ValueError("El nombre es obligatorio.")
        amount = CopAmountParser.parse(self._amount_entry.get())
        link_id = self._caption_to_cc_id.get(self._link_var.get(), "")
        return title, amount, link_id

    def _cancel(self) -> None:
        self._result = None
        self._shutdown()

    def _shutdown(self) -> None:
        if self._win is not None:
            self._win.destroy()
