"""Global CustomTkinter theme wiring."""

from __future__ import annotations

import customtkinter as ctk

from finanmind.ui.budget_ui_theme import BudgetUiTheme


class AppearanceConfigurator:
    """Sets appearance defaults shared by every Finanmind window."""

    @classmethod
    def apply_defaults(cls) -> None:
        """Force light chrome suited for a white workspace."""
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

    @classmethod
    def paint_main_surface(cls, window: ctk.CTk) -> None:
        """Paint the root window background pure white in both internal modes."""
        window.configure(fg_color=(BudgetUiTheme.BG_MAIN, BudgetUiTheme.BG_MAIN))
