"""Main layout with sidebar navigation and a central content host."""

from __future__ import annotations

from tkinter import messagebox

import customtkinter as ctk

from finanmind.budget.book_service import BudgetBookService
from finanmind.budget.repository_factory import BudgetRepositoryFactory
from finanmind.repositories.monthly_distribution_repository_factory import MonthlyDistributionRepositoryFactory
from finanmind.services.monthly_distribution_service import MonthlyDistributionService
from finanmind.ui.budget_management_window import BudgetManagementWindow
from finanmind.ui.monthly_distribution_window import MonthlyDistributionWindow


class ApplicationShell:
    """Hosts sidebar navigation and swaps primary feature panels."""

    def __init__(self, root: ctk.CTk) -> None:
        self._root = root
        self._content_host: ctk.CTkFrame | None = None
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

    def _configure_window_chrome(self) -> None:
        self._root.minsize(1000, 620)

    def _assemble_body(self) -> None:
        body = ctk.CTkFrame(self._root, fg_color=("#FFFFFF", "#FFFFFF"))
        body.pack(fill="both", expand=True)
        self._mount_sidebar(body)
        self._content_host = self._mount_content_host(body)

    def _mount_sidebar(self, body: ctk.CTkFrame) -> None:
        rail = ctk.CTkFrame(body, width=236, fg_color="#F1F5F9", corner_radius=0)
        rail.pack(side="left", fill="y")
        rail.pack_propagate(False)
        self._populate_sidebar(rail)

    def _mount_content_host(self, body: ctk.CTkFrame) -> ctk.CTkFrame:
        host = ctk.CTkFrame(body, fg_color=("#FFFFFF", "#FFFFFF"), corner_radius=0)
        host.pack(side="left", fill="both", expand=True)
        return host

    def _populate_sidebar(self, rail: ctk.CTkFrame) -> None:
        self._add_brand_block(rail)
        self._add_budget_button(rail)
        self._add_distribution_button(rail)
        self._add_future_button(rail, "Deudas")
        self._add_future_button(rail, "Ingresos")
        self._add_future_button(rail, "Metas")

    def _add_brand_block(self, rail: ctk.CTkFrame) -> None:
        title_font = ctk.CTkFont(size=21, weight="bold")
        title = ctk.CTkLabel(rail, text="Finanmind", font=title_font, text_color="#0f172a")
        title.pack(anchor="w", padx=22, pady=(26, 4))
        subtitle_font = ctk.CTkFont(size=12)
        subtitle = ctk.CTkLabel(
            rail,
            text="Finanzas personales",
            font=subtitle_font,
            text_color="#64748b",
        )
        subtitle.pack(anchor="w", padx=22, pady=(0, 10))

    def _add_budget_button(self, rail: ctk.CTkFrame) -> None:
        btn = ctk.CTkButton(
            rail,
            text="  Presupuesto",
            anchor="w",
            height=42,
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            text_color="#ffffff",
            command=self.show_budget_view,
        )
        btn.pack(fill="x", padx=14, pady=(16, 8))

    def _add_distribution_button(self, rail: ctk.CTkFrame) -> None:
        btn = ctk.CTkButton(
            rail,
            text="  Distribución mensual",
            anchor="w",
            height=42,
            fg_color="#0d9488",
            hover_color="#0f766e",
            text_color="#ffffff",
            command=self.show_monthly_distribution_view,
        )
        btn.pack(fill="x", padx=14, pady=4)

    def _add_future_button(self, rail: ctk.CTkFrame, caption: str) -> None:
        btn = ctk.CTkButton(
            rail,
            text=f"  {caption}",
            anchor="w",
            height=38,
            fg_color="transparent",
            hover_color="#e2e8f0",
            text_color="#475569",
            command=self._announce_future_feature,
        )
        btn.pack(fill="x", padx=14, pady=4)

    def _announce_future_feature(self) -> None:
        messagebox.showinfo("Finanmind", "Esta sección estará disponible próximamente.")

    def _purge_content_host(self) -> None:
        assert self._content_host is not None
        for child in self._content_host.winfo_children():
            child.destroy()
