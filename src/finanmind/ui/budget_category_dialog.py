"""Modal dialog for creating or editing budget categories."""

from __future__ import annotations

from tkinter import messagebox

import customtkinter as ctk

from finanmind.services.budget_category_palette import BudgetCategoryPalette


class BudgetCategoryDialog:
    """Collects category title and one preset card color."""

    def __init__(
        self,
        master: ctk.Misc,
        title: str,
        seed_card_color: str,
    ) -> None:
        self._master = master
        self._seed_title = title
        self._selection_color = seed_card_color.strip()
        self._result: tuple[str, str] | None = None
        self._win: ctk.CTkToplevel | None = None
        self._title_entry: ctk.CTkEntry | None = None
        self._tiles: list[tuple[ctk.CTkFrame, str]] = []
        self._active_tile: ctk.CTkFrame | None = None

    def show(self) -> tuple[str, str] | None:
        """Return ``(title, card_color_hex)`` when confirmed."""
        self._spawn_window()
        assert self._win is not None
        self._master.wait_window(self._win)
        return self._result

    def _spawn_window(self) -> None:
        win = ctk.CTkToplevel(self._master)
        self._win = win
        win.title("Categoría")
        win.geometry("780x640")
        win.minsize(680, 560)
        win.transient(self._master)
        win.grab_set()
        self._layout_shell(win)

    def _layout_shell(self, win: ctk.CTkToplevel) -> None:
        shell = ctk.CTkFrame(win, fg_color="#FFFFFF")
        shell.pack(fill="both", expand=True, padx=18, pady=18)
        self._mount_title_field(shell)
        self._mount_palette_section(shell)
        self._mount_footer(shell)

    def _mount_title_field(self, shell: ctk.CTkFrame) -> None:
        ctk.CTkLabel(shell, text="Nombre de la categoría").pack(anchor="w")
        entry = ctk.CTkEntry(shell, height=32)
        entry.pack(fill="x", pady=(4, 12))
        entry.insert(0, self._seed_title)
        self._title_entry = entry

    def _mount_palette_section(self, shell: ctk.CTkFrame) -> None:
        caption = "Elige el color de la tarjeta"
        ctk.CTkLabel(shell, text=caption).pack(anchor="w", pady=(0, 6))
        box = ctk.CTkScrollableFrame(shell, height=410, fg_color="#F1F5F9", corner_radius=12)
        box.pack(fill="both", expand=True, pady=(0, 12))
        self._fill_palette(box)
        self._highlight_initial_tile()

    def _mount_footer(self, shell: ctk.CTkFrame) -> None:
        row = ctk.CTkFrame(shell, fg_color="transparent")
        row.pack(fill="x", pady=(12, 4))
        btn_height = 38
        cancel_btn = ctk.CTkButton(row, text="Cancelar", width=130, height=btn_height, command=self._cancel)
        cancel_btn.pack(side="right")
        save_btn = ctk.CTkButton(row, text="Guardar", width=130, height=btn_height, command=self._confirm)
        save_btn.pack(side="right", padx=(0, 12))

    def _fill_palette(self, box: ctk.CTkScrollableFrame) -> None:
        holder = ctk.CTkFrame(box, fg_color="transparent")
        holder.pack(fill="both", expand=True)
        row_frame = None
        for idx, tone in enumerate(BudgetCategoryPalette.PRESETS):
            if idx % 2 == 0:
                row_frame = ctk.CTkFrame(holder, fg_color="transparent")
                row_frame.pack(fill="x", pady=4)
            assert row_frame is not None
            self._add_color_tile(row_frame, tone)

    def _add_color_tile(self, row: ctk.CTkFrame, tone: str) -> None:
        outer = ctk.CTkFrame(row, fg_color="#FFFFFF", corner_radius=12, border_width=2, border_color="#E2E8F0")
        outer.pack(side="left", expand=True, fill="x", padx=6)
        chip = ctk.CTkFrame(outer, width=96, height=44, fg_color=tone, corner_radius=10)
        chip.pack(padx=14, pady=14)
        self._tiles.append((outer, tone))
        pick = lambda _evt, shell=outer, value=tone: self._select_color(shell, value)
        self._bind_pick_chain(outer, pick)

    def _bind_pick_chain(self, widget: ctk.Misc, handler) -> None:
        widget.bind("<Button-1>", handler)
        for child in widget.winfo_children():
            self._bind_pick_chain(child, handler)

    def _select_color(self, shell: ctk.CTkFrame, tone: str) -> None:
        self._clear_active_border()
        self._active_tile = shell
        shell.configure(border_color="#2563EB", border_width=3)
        self._selection_color = tone

    def _clear_active_border(self) -> None:
        if self._active_tile is None:
            return
        self._active_tile.configure(border_color="#E2E8F0", border_width=2)

    def _highlight_initial_tile(self) -> None:
        seed = self._normalized_hex(self._selection_color)
        if seed == "":
            return
        for outer, tone in self._tiles:
            if self._normalized_hex(tone) == seed:
                self._select_color(outer, tone)
                return

    def _normalized_hex(self, value: str) -> str:
        return value.strip().lstrip("#").upper()

    def _confirm(self) -> None:
        assert self._title_entry is not None
        title = self._title_entry.get().strip()
        if title == "":
            messagebox.showwarning("Categoría", "Escribe un nombre para la categoría.")
            return
        if self._selection_color.strip() == "":
            messagebox.showwarning("Categoría", "Selecciona un color de la paleta.")
            return
        self._result = (title, self._selection_color.strip())
        self._close_window()

    def _cancel(self) -> None:
        self._result = None
        self._close_window()

    def _close_window(self) -> None:
        if self._win is not None:
            self._win.destroy()
