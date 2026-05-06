"""First-run screen that configures where CSV datasets are stored."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from finanmind.services.user_data_path_service import UserDataPathService
from finanmind.ui.window_startup import MainWindowPlacement


class WorkspaceSetupScreen:
    """Primary-window wizard shown until the workspace folder is chosen."""

    def __init__(self, master: ctk.CTk, path_service: UserDataPathService) -> None:
        self._master = master
        self._service = path_service
        self._chosen: Path | None = None
        self._done = tk.BooleanVar(value=False)
        self._shell: ctk.CTkFrame | None = None
        self._entry: ctk.CTkEntry | None = None

    def run_modal(self) -> Path | None:
        """Process UI events until the user confirms or exits."""
        self._prepare_master()
        self._build_shell()
        self._master.wait_variable(self._done)
        return self._chosen

    def _prepare_master(self) -> None:
        self._master.configure(fg_color=("#FFFFFF", "#FFFFFF"))
        self._master.title("Finanmind — Primera configuración")
        MainWindowPlacement.apply_maximized(self._master, min_width=660, min_height=440)

    def _build_shell(self) -> None:
        outer = ctk.CTkFrame(self._master, fg_color="#FFFFFF")
        outer.pack(fill="both", expand=True, padx=36, pady=36)
        self._shell = outer
        self._add_heading(outer)
        self._add_instructions(outer)
        self._add_path_row(outer)
        self._add_actions(outer)

    def _add_heading(self, outer: ctk.CTkFrame) -> None:
        self._add_main_title(outer)
        self._add_subtitle(outer)

    def _add_main_title(self, outer: ctk.CTkFrame) -> None:
        font = ctk.CTkFont(size=22, weight="bold")
        label = ctk.CTkLabel(
            outer,
            text="Indica dónde guardaremos tus datos",
            font=font,
            justify="left",
        )
        label.pack(anchor="w")

    def _add_subtitle(self, outer: ctk.CTkFrame) -> None:
        font = ctk.CTkFont(size=14)
        label = ctk.CTkLabel(
            outer,
            text="Los CSV quedan fuera del programa; elige una carpeta clara para ti.",
            font=font,
            wraplength=640,
            justify="left",
            text_color=("gray30", "gray70"),
        )
        label.pack(anchor="w", pady=(10, 6))

    def _add_instructions(self, outer: ctk.CTkFrame) -> None:
        lines = (
            "Es obligatorio la primera vez: sin una ruta no puede guardarse nada.",
            "Puedes usar Documentos o cualquier carpeta que prefieras.",
            "Podrás respaldar copiando esa carpeta cuando quieras.",
        )
        hint_font = ctk.CTkFont(size=13)
        for line in lines:
            bullet = ctk.CTkLabel(outer, text=f"• {line}", font=hint_font, justify="left")
            bullet.pack(anchor="w", pady=4)

    def _add_path_row(self, outer: ctk.CTkFrame) -> None:
        row = ctk.CTkFrame(outer, fg_color="transparent")
        row.pack(fill="x", pady=(22, 10))
        suggested = str(self._service.suggested_documents_folder())
        entry = ctk.CTkEntry(row, height=42, corner_radius=10, placeholder_text="Ruta de la carpeta…")
        entry.pack(side="left", fill="x", expand=True, padx=(0, 12))
        entry.insert(0, suggested)
        self._entry = entry
        browse_btn = ctk.CTkButton(row, text="Examinar…", width=120, command=self._browse)
        browse_btn.pack(side="left")

    def _add_actions(self, outer: ctk.CTkFrame) -> None:
        row = ctk.CTkFrame(outer, fg_color="transparent")
        row.pack(fill="x", pady=(22, 0))
        confirm_btn = ctk.CTkButton(row, text="Guardar y continuar", width=200, command=self._confirm)
        confirm_btn.pack(side="right")
        exit_btn = ctk.CTkButton(
            row,
            text="Salir",
            width=110,
            fg_color=("gray70", "gray35"),
            hover_color=("gray55", "gray45"),
            command=self._cancel,
        )
        exit_btn.pack(side="right", padx=(0, 12))

    def _browse(self) -> None:
        assert self._entry is not None
        picked = filedialog.askdirectory(initialdir=self._entry.get())
        if picked:
            self._entry.delete(0, "end")
            self._entry.insert(0, picked)

    def _confirm(self) -> None:
        assert self._entry is not None
        raw_text = self._entry.get().strip()
        if not raw_text:
            messagebox.showwarning("Ruta requerida", "Escribe o selecciona una carpeta.")
            return
        target = Path(raw_text)
        self._service.persist_root(target)
        self._chosen = target
        self._tear_down()

    def _cancel(self) -> None:
        self._chosen = None
        self._tear_down()

    def _tear_down(self) -> None:
        if self._shell is not None:
            self._shell.destroy()
            self._shell = None
        self._done.set(True)
