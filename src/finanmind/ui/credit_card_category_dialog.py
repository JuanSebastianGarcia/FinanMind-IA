"""Modal dialog for adding or editing an expense category."""

from __future__ import annotations

from tkinter import messagebox

import customtkinter as ctk

from finanmind.budget.palette import BudgetCategoryPalette
from finanmind.ui.budget_ui_theme import BudgetUiTheme


class CreditCardCategoryDialog:
    """Collects title and color for a per-card expense category."""

    _NO_LINK_CAPTION = "Sin enlace"

    def __init__(
        self,
        master: ctk.Misc,
        title_text: str,
        seed_title: str,
        seed_color: str,
        *,
        link_options: list[tuple[str, str]] | None = None,
        seed_link_id: str = "",
    ) -> None:
        self._master = master
        self._title_text = title_text
        self._seed_title = seed_title
        self._result: tuple[str, str, str] | None = None
        self._win: ctk.CTkToplevel | None = None
        self._title_entry: ctk.CTkEntry | None = None
        self._color_var = ctk.StringVar(value=seed_color or BudgetCategoryPalette.PRESETS[0])
        self._link_options = list(link_options or [])
        self._caption_to_label_id = self._build_link_map(self._link_options)
        self._link_var = ctk.StringVar(value=self._initial_link_caption(seed_link_id))

    def show(self) -> tuple[str, str, str] | None:
        """Return ``(title, color, linked_label_id)`` when confirmed."""
        self._spawn_window()
        assert self._win is not None
        self._master.wait_window(self._win)
        return self._result

    def _build_link_map(self, options: list[tuple[str, str]]) -> dict[str, str]:
        out = {self._NO_LINK_CAPTION: ""}
        for caption, label_id in options:
            out[caption] = label_id
        return out

    def _initial_link_caption(self, seed_link_id: str) -> str:
        token = seed_link_id.strip()
        for caption, label_id in self._caption_to_label_id.items():
            if label_id == token and token != "":
                return caption
        return self._NO_LINK_CAPTION

    def _spawn_window(self) -> None:
        win = ctk.CTkToplevel(self._master)
        self._win = win
        win.title(self._title_text)
        win.geometry("460x320" if self._link_options else "440x250")
        win.transient(self._master)
        win.grab_set()
        win.configure(fg_color=BudgetUiTheme.BG_CARD)
        self._build(win)

    def _build(self, win: ctk.CTkToplevel) -> None:
        shell = ctk.CTkFrame(win, fg_color=BudgetUiTheme.BG_CARD)
        shell.pack(fill="both", expand=True, padx=18, pady=18)
        self._mount_title_field(shell)
        self._mount_color_row(shell)
        if self._link_options:
            self._mount_link_row(shell)
        self._mount_action_row(shell)
        self._bind_return_save()

    def _mount_title_field(self, shell: ctk.CTkFrame) -> None:
        ctk.CTkLabel(shell, text="Nombre", text_color=BudgetUiTheme.TXT_SEC, anchor="w").pack(anchor="w")
        entry = ctk.CTkEntry(
            shell,
            height=32,
            fg_color=BudgetUiTheme.BG_MAIN,
            border_color=BudgetUiTheme.BORDER,
            text_color=BudgetUiTheme.TXT_PRI,
        )
        entry.pack(fill="x", pady=(4, 10))
        entry.insert(0, self._seed_title)
        self._title_entry = entry

    def _mount_color_row(self, shell: ctk.CTkFrame) -> None:
        ctk.CTkLabel(shell, text="Color", text_color=BudgetUiTheme.TXT_SEC, anchor="w").pack(anchor="w")
        wrap = ctk.CTkFrame(shell, fg_color="transparent")
        wrap.pack(fill="x", pady=(4, 12))
        for color in BudgetCategoryPalette.PRESETS:
            self._mount_color_chip(wrap, color)

    def _mount_color_chip(self, wrap: ctk.CTkFrame, color: str) -> None:
        ctk.CTkButton(
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
        ).pack(side="left", padx=2)

    def _mount_link_row(self, shell: ctk.CTkFrame) -> None:
        self._mount_link_caption(shell)
        self._mount_link_menu(shell)

    def _mount_link_caption(self, shell: ctk.CTkFrame) -> None:
        ctk.CTkLabel(
            shell,
            text="Vincular a etiqueta del presupuesto",
            text_color=BudgetUiTheme.TXT_SEC,
            anchor="w",
        ).pack(anchor="w")

    def _mount_link_menu(self, shell: ctk.CTkFrame) -> None:
        ctk.CTkOptionMenu(
            shell,
            variable=self._link_var,
            values=list(self._caption_to_label_id.keys()),
            fg_color=BudgetUiTheme.BG_MAIN,
            button_color=BudgetUiTheme.BORDER,
            button_hover_color=BudgetUiTheme.TXT_TER,
            dropdown_fg_color=BudgetUiTheme.BG_CARD,
            dropdown_text_color=BudgetUiTheme.TXT_PRI,
            text_color=BudgetUiTheme.TXT_PRI,
            height=32,
        ).pack(fill="x", pady=(4, 12))

    def _mount_action_row(self, shell: ctk.CTkFrame) -> None:
        row = ctk.CTkFrame(shell, fg_color="transparent")
        row.pack(fill="x", pady=(8, 0))
        self._make_secondary(row, "Cancelar", self._cancel).pack(side="right")
        self._make_primary(row, "Guardar", self._confirm).pack(side="right", padx=(0, 10))

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

    def _bind_return_save(self) -> None:
        assert self._title_entry is not None
        self._title_entry.bind("<Return>", self._on_return_save)

    def _on_return_save(self, _event: object) -> None:
        self._confirm()

    def _confirm(self) -> None:
        assert self._title_entry is not None
        title = self._title_entry.get().strip()
        if title == "":
            messagebox.showwarning("Categoría", "El nombre es obligatorio.")
            return
        link_id = self._caption_to_label_id.get(self._link_var.get(), "")
        self._result = (title, self._color_var.get(), link_id)
        self._shutdown()

    def _cancel(self) -> None:
        self._result = None
        self._shutdown()

    def _shutdown(self) -> None:
        if self._win is not None:
            self._win.destroy()
