"""Aggregates the entire Investments panel snapshot in a single JSON dict."""

from __future__ import annotations

from finanmind.models.investment_currency_code import InvestmentCurrencyCode
from finanmind.services.investment_portfolio_analytics import InvestmentPortfolioAnalytics
from finanmind.services.investment_service import InvestmentService
from finanmind.ui.web.bridges.investment_categories_builder import (
    InvestmentCategoriesBuilder,
)
from finanmind.ui.web.bridges.investment_distribution_builder import (
    InvestmentDistributionBuilder,
)
from finanmind.ui.web.bridges.investment_entries_builder import (
    InvestmentEntriesBuilder,
)
from finanmind.ui.web.bridges.investment_summary_builder import (
    InvestmentSummaryBuilder,
)


class InvestmentStateBuilder:
    """Builds the full investments dashboard state in one snapshot."""

    @classmethod
    def build(cls, service: InvestmentService) -> dict:
        """Return summary, entry rows, categories and distribution per currency."""
        analytics = cls._make_analytics(service)
        return {
            "summary": InvestmentSummaryBuilder.build(analytics),
            "entries": InvestmentEntriesBuilder.build(service.entries_snapshot(), analytics),
            "categories": InvestmentCategoriesBuilder.build(service.categories_snapshot()),
            "distribution_cop": InvestmentDistributionBuilder.build(analytics, InvestmentCurrencyCode.COP),
            "distribution_usd": InvestmentDistributionBuilder.build(analytics, InvestmentCurrencyCode.USD),
        }

    @classmethod
    def _make_analytics(cls, service: InvestmentService) -> InvestmentPortfolioAnalytics:
        return InvestmentPortfolioAnalytics(
            service.entries_snapshot(),
            service.categories_snapshot(),
        )
