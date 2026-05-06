"""Tk workflow entry that wires workspace checks and main panels."""

from __future__ import annotations

from pathlib import Path

import customtkinter as ctk

from finanmind.config import AppConfig
from finanmind.repositories.workspace_settings_repository import WorkspaceSettingsRepository
from finanmind.services.user_data_path_service import UserDataPathService
from finanmind.ui.application_shell import ApplicationShell
from finanmind.ui.appearance_configurator import AppearanceConfigurator
from finanmind.ui.workspace_setup_screen import WorkspaceSetupScreen


class DesktopRunner:
    """Coordinates Tk bootstrap, workspace folder setup, and main screens."""

    def run(self) -> None:
        """Launch the desktop shell when the user completes prerequisites."""
        AppearanceConfigurator.apply_defaults()
        root = ctk.CTk()
        AppearanceConfigurator.paint_main_surface(root)
        repository = WorkspaceSettingsRepository.create_default()
        path_service = UserDataPathService(repository)
        if not self._apply_saved_workspace(path_service):
            chosen = self._run_workspace_screen(root, path_service)
            if chosen is None:
                root.destroy()
                return
        shell = ApplicationShell(root)
        shell.present_initial_panel()
        self._focus_root(root)
        root.mainloop()

    def _run_workspace_screen(
        self,
        root: ctk.CTk,
        path_service: UserDataPathService,
    ) -> Path | None:
        screen = WorkspaceSetupScreen(root, path_service)
        return screen.run_modal()

    def _focus_root(self, root: ctk.CTk) -> None:
        root.lift()
        root.focus_force()

    def _apply_saved_workspace(self, path_service: UserDataPathService) -> bool:
        saved_root = path_service.load_configured_root()
        if saved_root is None:
            return False
        AppConfig.USER_DATA_ROOT = saved_root
        return True
