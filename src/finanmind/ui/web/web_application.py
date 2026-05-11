"""Boots PyWebview and wires the Budget services to the JavaScript layer."""

from __future__ import annotations

import webview

from finanmind.budget.book_service import BudgetBookService
from finanmind.budget.repository_factory import BudgetRepositoryFactory
from finanmind.repositories.credit_card_repository_factory import CreditCardRepositoryFactory
from finanmind.repositories.monthly_distribution_repository_factory import (
    MonthlyDistributionRepositoryFactory,
)
from finanmind.services.credit_card_service import CreditCardService
from finanmind.services.monthly_distribution_service import MonthlyDistributionService
from finanmind.ui.web.bridges.budget_bridge import BudgetBridge
from finanmind.ui.web.bridges.distribution_bridge import DistributionBridge
from finanmind.ui.web.frontend_assets import FrontendAssetsLocator
from finanmind.ui.web.js_api import JsApi
from finanmind.ui.web.web_window_config import WebWindowConfig


class WebApplication:
    """Creates the native chromium window and serves the bundled web UI."""

    @classmethod
    def run(cls) -> None:
        """Start PyWebview blocking on the rendered window's lifecycle."""
        api = cls._build_api()
        config = WebWindowConfig.default()
        index_path = FrontendAssetsLocator.find_index_path()
        cls._create_window(index_path, api, config)
        webview.start(http_server=True, debug=config.debug)

    @classmethod
    def _build_api(cls) -> JsApi:
        book = cls._make_book_service()
        cards = cls._make_cards_service()
        ledger = cls._make_distribution_service()
        return JsApi(BudgetBridge(book, cards), DistributionBridge(book, ledger))

    @classmethod
    def _make_book_service(cls) -> BudgetBookService:
        service = BudgetBookService(BudgetRepositoryFactory.from_app_config())
        service.load()
        return service

    @classmethod
    def _make_cards_service(cls) -> CreditCardService:
        service = CreditCardService(CreditCardRepositoryFactory.from_app_config())
        service.load()
        return service

    @classmethod
    def _make_distribution_service(cls) -> MonthlyDistributionService:
        service = MonthlyDistributionService(MonthlyDistributionRepositoryFactory.from_app_config())
        service.load()
        return service

    @classmethod
    def _create_window(cls, index_path: str, api: JsApi, config: WebWindowConfig) -> None:
        webview.create_window(
            title=config.title,
            url=index_path,
            js_api=api,
            width=config.width,
            height=config.height,
            min_size=(config.min_width, config.min_height),
            maximized=config.maximized,
        )
