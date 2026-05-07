"""Main layout with sidebar navigation and a central content host."""

from __future__ import annotations

from tkinter import messagebox

import customtkinter as ctk

from finanmind.budget.book_service import BudgetBookService
from finanmind.budget.repository_factory import BudgetRepositoryFactory
from finanmind.repositories.monthly_distribution_repository_factory import MonthlyDistributionRepositoryFactory
from finanmind.services.monthly_distribution_service import MonthlyDistributionService
from finanmind.ui.budget_management_window import BudgetManagementWindow
from finanmind.ui.budget_ui_theme import BudgetUiTheme
from finanmind.ui.monthly_distribution_window import MonthlyDistributionWindow


class ApplicationShell:
    """Hosts sidebar navigation and swaps primary feature panels."""

    def __init__(self, root: ctk.CTk) -> None:
        self._root = root
        self._content_host: ctk.CTkFrame | None = None
        self._budget_nav_btn: ctk.CTkButton | None = None
        self._dist_nav_btn: ctk.CTkButton | None = None
        self._active_panel = "budget"
        self._configure_window_chrome()
        self._assemble_body()

    def present_initial_panel(self) -> None:
        """Load the default starting module after authentication/setup."""
        self.show_budget_view()

    def show_budget_view(self) -> None:
        """Mount the budget overview inside the white content surface."""
        assert self._content_host is not None
        self._root.title("Finanmind — Presupuesto")
        self._purge_content_host()
        repo = BudgetRepositoryFactory.from_app_config()
        budget_book = BudgetBookService(repo)
        budget_book.load()
        viewer = BudgetManagementWindow(self._content_host, budget_book)
        viewer.attach()
        self._active_panel = "budget"
        self._apply_nav_styles()

    def show_monthly_distribution_view(self) -> None:
        """Mount the payroll distribution ledger versus budget tags."""
        assert self._content_host is not None
        self._root.title("Finanmind — Distribución mensual")
        self._purge_content_host()
        budget_repo = BudgetRepositoryFactory.from_app_config()
        ledger_repo = MonthlyDistributionRepositoryFactory.from_app_config()
        budget_book = BudgetBookService(budget_repo)
        ledger = MonthlyDistributionService(ledger_repo)
        viewer = MonthlyDistributionWindow(self._content_host, budget_book, ledger)
        viewer.attach()
        self._active_panel = "distribution"
        self._apply_nav_styles()

    def _configure_window_chrome(self) -> None:
        self._root.minsize(1000, 620)

    def _assemble_body(self) -> None:
        body = ctk.CTkFrame(self._root, fg_color=(BudgetUiTheme.BG_MAIN, BudgetUiTheme.BG_MAIN))
        body.pack(fill="both", expand=True)
        self._mount_sidebar(body)
        self._content_host = self._mount_content_host(body)

    def _mount_sidebar(self, body: ctk.CTkFrame) -> None:
        rail = ctk.CTkFrame(body, width=236, fg_color=BudgetUiTheme.SIDEBAR_BG, corner_radius=0)
        rail.pack(side="left", fill="y")
        rail.pack_propagate(False)
        self._populate_sidebar(rail)

    def _mount_content_host(self, body: ctk.CTkFrame) -> ctk.CTkFrame:
        host = ctk.CTkFrame(body, fg_color=(BudgetUiTheme.BG_MAIN, BudgetUiTheme.BG_MAIN), corner_radius=0)
        host.pack(side="left", fill="both", expand=True)
        return host

    def _populate_sidebar(self, rail: ctk.CTkFrame) -> None:
        self._add_brand_block(rail)
        self._add_budget_button(rail)
        self._add_distribution_button(rail)
        self._add_future_button(rail, "Deudas")
        self._add_future_button(rail, "Ingresos")
        self._add_future_button(rail, "Metas")
        self._add_sidebar_footer(rail)
        self._apply_nav_styles()

    def _add_sidebar_footer(self, rail: ctk.CTkFrame) -> None:
        foot_font = ctk.CTkFont(size=10)
        lbl = ctk.CTkLabel(rail, text="budget.csv · COP", font=foot_font, text_color=BudgetUiTheme.SIDEBAR_MUTE)
        lbl.pack(side="bottom", anchor="w", padx=16, pady=14)

    def _apply_nav_styles(self) -> None:
        if self._budget_nav_btn is None or self._dist_nav_btn is None:
            return
        active_bg = BudgetUiTheme.SIDEBAR_ACTIVE_BG
        muted = BudgetUiTheme.SIDEBAR_MUTE
        lit = BudgetUiTheme.SIDEBAR_TXT
        b_on = self._active_panel == "budget"
        d_on = self._active_panel == "distribution"
        self._budget_nav_btn.configure(fg_color=active_bg if b_on else "transparent", text_color=lit if b_on else muted)
        self._dist_nav_btn.configure(fg_color=active_bg if d_on else "transparent", text_color=lit if d_on else muted)

    def _add_brand_block(self, rail: ctk.CTkFrame) -> None:
        brand = ctk.CTkFrame(rail, fg_color="transparent")
        brand.pack(fill="x", padx=16, pady=(20, 12))
        title_font = ctk.CTkFont(size=17, weight="bold")
        title = ctk.CTkLabel(brand, text="Finanmind", font=title_font, text_color=BudgetUiTheme.SIDEBAR_TXT)
        title.pack(anchor="w")
        sub_font = ctk.CTkFont(size=11)
        subtitle = ctk.CTkLabel(brand, text="Finanzas personales", font=sub_font, text_color=BudgetUiTheme.SIDEBAR_MUTE)
        subtitle.pack(anchor="w")
        rule = ctk.CTkFrame(rail, fg_color="#2d3748", height=1)
        rule.pack(fill="x", pady=(0, 10))

    def _add_budget_button(self, rail: ctk.CTkFrame) -> None:
        btn = ctk.CTkButton(
            rail,
            text="  Presupuesto",
            anchor="w",
            font=ctk.CTkFont(size=13),
            height=38,
            fg_color="transparent",
            hover_color=BudgetUiTheme.SIDEBAR_ACTIVE_BG,
            text_color=BudgetUiTheme.SIDEBAR_MUTE,
            border_width=0,
            corner_radius=8,
            command=self.show_budget_view,
        )
        btn.pack(fill="x", padx=8, pady=1)
        self._budget_nav_btn = btn

    def _add_distribution_button(self, rail: ctk.CTkFrame) -> None:
        btn = ctk.CTkButton(
            rail,
            text="  Distribución mensual",
            anchor="w",
            font=ctk.CTkFont(size=13),
            height=38,
            fg_color="transparent",
            hover_color=BudgetUiTheme.SIDEBAR_ACTIVE_BG,
            text_color=BudgetUiTheme.SIDEBAR_MUTE,
            border_width=0,
            corner_radius=8,
            command=self.show_monthly_distribution_view,
        )
        btn.pack(fill="x", padx=8, pady=1)
        self._dist_nav_btn = btn

    def _add_future_button(self, rail: ctk.CTkFrame, caption: str) -> None:
        btn = ctk.CTkButton(
            rail,
            text=f"  {caption}",
            anchor="w",
            height=38,
            fg_color="transparent",
            hover_color=BudgetUiTheme.SIDEBAR_ACTIVE_BG,
            text_color=BudgetUiTheme.SIDEBAR_MUTE,
            border_width=0,
            corner_radius=8,
            command=self._announce_future_feature,
        )
        btn.pack(fill="x", padx=8, pady=1)

    def _announce_future_feature(self) -> None:
        messagebox.showinfo("Finanmind", "Esta sección estará disponible próximamente.")

    def _purge_content_host(self) -> None:
        assert self._content_host is not None
        for child in self._content_host.winfo_children():
            child.destroy()
