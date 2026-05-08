"""Main layout with sidebar navigation and a central content host."""

from __future__ import annotations

from tkinter import messagebox

import customtkinter as ctk

from finanmind.budget.book_service import BudgetBookService
from finanmind.budget.repository_factory import BudgetRepositoryFactory
from finanmind.repositories.credit_card_repository_factory import CreditCardRepositoryFactory
from finanmind.repositories.monthly_distribution_repository_factory import MonthlyDistributionRepositoryFactory
from finanmind.services.credit_card_service import CreditCardService
from finanmind.services.monthly_distribution_service import MonthlyDistributionService
from finanmind.ui.budget_management_window import BudgetManagementWindow
from finanmind.ui.budget_review_window import BudgetReviewWindow
from finanmind.ui.budget_ui_theme import BudgetUiTheme
from finanmind.ui.credit_cards_router import CreditCardsRouter
from finanmind.ui.monthly_distribution_window import MonthlyDistributionWindow


class ApplicationShell:
    """Hosts sidebar navigation; both panels stay placed and switch via z-order."""

    def __init__(self, root: ctk.CTk) -> None:
        self._root = root
        self._init_navigation_state()
        self._init_panel_handles()
        self._shared_book = self._make_shared_book()
        self._ledger = self._make_ledger()
        self._cards_service = self._make_cards_service()
        self._configure_window_chrome()
        self._assemble_body()

    def _init_navigation_state(self) -> None:
        self._content_host: ctk.CTkFrame | None = None
        self._budget_nav_btn: ctk.CTkButton | None = None
        self._dist_nav_btn: ctk.CTkButton | None = None
        self._cards_nav_btn: ctk.CTkButton | None = None
        self._active_panel = "budget"

    def _init_panel_handles(self) -> None:
        self._budget_layer: ctk.CTkFrame | None = None
        self._dist_layer: ctk.CTkFrame | None = None
        self._cards_layer: ctk.CTkFrame | None = None
        self._review_layer: ctk.CTkFrame | None = None
        self._budget_viewer: BudgetManagementWindow | None = None
        self._dist_viewer: MonthlyDistributionWindow | None = None
        self._cards_router: CreditCardsRouter | None = None
        self._review_viewer: BudgetReviewWindow | None = None

    def present_initial_panel(self) -> None:
        """Build all panels once and show the budget overview on top."""
        self._build_budget_layer()
        self._build_dist_layer()
        self._build_cards_layer()
        self._build_review_layer()
        self.show_budget_view()

    def show_credit_cards_view(self) -> None:
        """Lift the credit-cards panel; widgets are reused, only z-order changes."""
        assert self._cards_layer is not None and self._cards_router is not None
        self._root.title("Finanmind — Tarjetas de crédito")
        self._cards_router.refresh()
        self._cards_layer.lift()
        self._active_panel = "cards"
        self._apply_nav_styles()

    def show_budget_view(self) -> None:
        """Lift the budget panel; widgets are reused, only z-order changes."""
        assert self._budget_layer is not None and self._budget_viewer is not None
        self._root.title("Finanmind — Presupuesto")
        self._budget_viewer.refresh()
        self._budget_layer.lift()
        self._active_panel = "budget"
        self._apply_nav_styles()

    def show_monthly_distribution_view(self) -> None:
        """Lift the distribution panel; widgets are reused, only z-order changes."""
        assert self._dist_layer is not None and self._dist_viewer is not None
        self._root.title("Finanmind — Distribución mensual")
        self._dist_viewer.refresh()
        self._dist_layer.lift()
        self._active_panel = "distribution"
        self._apply_nav_styles()

    def show_budget_review_view(self) -> None:
        """Lift the AI review panel; resets transient state on each entry."""
        assert self._review_layer is not None and self._review_viewer is not None
        self._root.title("Finanmind — Revisión IA")
        self._review_viewer.reset()
        self._review_layer.lift()
        self._active_panel = "review"
        self._apply_nav_styles()

    def _make_shared_book(self) -> BudgetBookService:
        book = BudgetBookService(BudgetRepositoryFactory.from_app_config())
        book.load()
        return book

    def _make_ledger(self) -> MonthlyDistributionService:
        ledger = MonthlyDistributionService(MonthlyDistributionRepositoryFactory.from_app_config())
        ledger.load()
        return ledger

    def _make_cards_service(self) -> CreditCardService:
        service = CreditCardService(CreditCardRepositoryFactory.from_app_config())
        service.load()
        return service

    def _build_budget_layer(self) -> None:
        assert self._content_host is not None
        layer = ctk.CTkFrame(self._content_host, fg_color=BudgetUiTheme.BG_MAIN, corner_radius=0)
        layer.place(x=0, y=0, relwidth=1, relheight=1)
        viewer = BudgetManagementWindow(layer, self._shared_book, on_open_review=self.show_budget_review_view)
        viewer.attach()
        self._budget_layer = layer
        self._budget_viewer = viewer

    def _build_review_layer(self) -> None:
        assert self._content_host is not None
        layer = ctk.CTkFrame(self._content_host, fg_color=BudgetUiTheme.BG_MAIN, corner_radius=0)
        layer.place(x=0, y=0, relwidth=1, relheight=1)
        viewer = BudgetReviewWindow(
            layer,
            self._shared_book,
            on_back=self.show_budget_view,
            on_budget_changed=self._handle_budget_changed_externally,
        )
        viewer.attach()
        self._review_layer = layer
        self._review_viewer = viewer

    def _handle_budget_changed_externally(self) -> None:
        if self._budget_viewer is not None:
            self._budget_viewer.refresh()

    def _build_dist_layer(self) -> None:
        assert self._content_host is not None
        layer = ctk.CTkFrame(self._content_host, fg_color=BudgetUiTheme.BG_MAIN, corner_radius=0)
        layer.place(x=0, y=0, relwidth=1, relheight=1)
        viewer = MonthlyDistributionWindow(layer, self._shared_book, self._ledger)
        viewer.attach()
        self._dist_layer = layer
        self._dist_viewer = viewer

    def _build_cards_layer(self) -> None:
        assert self._content_host is not None
        layer = ctk.CTkFrame(self._content_host, fg_color=BudgetUiTheme.BG_MAIN, corner_radius=0)
        layer.place(x=0, y=0, relwidth=1, relheight=1)
        router = CreditCardsRouter(layer, self._cards_service)
        router.attach()
        self._cards_layer = layer
        self._cards_router = router

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
        self._add_credit_cards_button(rail)
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
        self._tint_nav_button(self._budget_nav_btn, "budget", active_bg, lit, muted)
        self._tint_nav_button(self._dist_nav_btn, "distribution", active_bg, lit, muted)
        self._tint_nav_button(self._cards_nav_btn, "cards", active_bg, lit, muted)

    def _tint_nav_button(
        self,
        btn: ctk.CTkButton | None,
        target_key: str,
        active_bg: str,
        active_fg: str,
        muted_fg: str,
    ) -> None:
        if btn is None:
            return
        on = self._active_panel == target_key
        btn.configure(
            fg_color=active_bg if on else "transparent",
            text_color=active_fg if on else muted_fg,
        )

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

    def _add_credit_cards_button(self, rail: ctk.CTkFrame) -> None:
        btn = ctk.CTkButton(
            rail,
            text="  Deudas",
            anchor="w",
            font=ctk.CTkFont(size=13),
            height=38,
            fg_color="transparent",
            hover_color=BudgetUiTheme.SIDEBAR_ACTIVE_BG,
            text_color=BudgetUiTheme.SIDEBAR_MUTE,
            border_width=0,
            corner_radius=8,
            command=self.show_credit_cards_view,
        )
        btn.pack(fill="x", padx=8, pady=1)
        self._cards_nav_btn = btn

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
