"""Builds the 4 summary chips (COP total, USD total, entry count, category count)."""

from __future__ import annotations

from finanmind.models.investment_currency_code import InvestmentCurrencyCode
from finanmind.services.investment_portfolio_analytics import InvestmentPortfolioAnalytics


class InvestmentSummaryBuilder:
    """Serialises the investments header strip into a JSON payload."""

    @classmethod
    def build(cls, analytics: InvestmentPortfolioAnalytics) -> dict:
        """Return totals per currency and counters for the dashboard strip."""
        return {
            "total_cop": analytics.total_for_currency(InvestmentCurrencyCode.COP),
            "total_usd": analytics.total_for_currency(InvestmentCurrencyCode.USD),
            "entry_count": analytics.entry_count(),
            "category_count": analytics.defined_category_count(),
        }
