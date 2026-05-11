"""Bootstrap that ensures a workspace folder exists and launches the web UI."""

from __future__ import annotations

from pathlib import Path

import customtkinter as ctk

from finanmind.config import AppConfig
from finanmind.repositories.workspace_settings_repository import WorkspaceSettingsRepository
from finanmind.services.user_data_path_service import UserDataPathService
from finanmind.ui.appearance_configurator import AppearanceConfigurator
from finanmind.ui.web.web_application import WebApplication
from finanmind.ui.workspace_setup_screen import WorkspaceSetupScreen


class DesktopRunner:
    """Wires first-run workspace setup (Tk) and the main web window (PyWebview)."""

    def run(self) -> None:
        """Launch the desktop shell when the user completes prerequisites."""
        AppearanceConfigurator.apply_defaults()
        if not self._ensure_workspace_configured():
            return
        WebApplication.run()

    def _ensure_workspace_configured(self) -> bool:
        repository = WorkspaceSettingsRepository.create_default()
        path_service = UserDataPathService(repository)
        if self._apply_saved_workspace(path_service):
            return True
        return self._collect_workspace_via_tk(path_service)

    def _collect_workspace_via_tk(self, path_service: UserDataPathService) -> bool:
        root = ctk.CTk()
        AppearanceConfigurator.paint_main_surface(root)
        try:
            chosen = self._run_workspace_screen(root, path_service)
        finally:
            root.destroy()
        return chosen is not None

    def _run_workspace_screen(
        self,
        root: ctk.CTk,
        path_service: UserDataPathService,
    ) -> Path | None:
        screen = WorkspaceSetupScreen(root, path_service)
        return screen.run_modal()

    def _apply_saved_workspace(self, path_service: UserDataPathService) -> bool:
        saved_root = path_service.load_configured_root()
        if saved_root is None:
            return False
        AppConfig.USER_DATA_ROOT = saved_root
        return True
