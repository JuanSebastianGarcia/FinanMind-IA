"""Builds donut slices per currency with palette colors for the chart and legend."""

from __future__ import annotations

from finanmind.services.investment_portfolio_analytics import InvestmentPortfolioAnalytics
from finanmind.ui.investment_chart_palette import InvestmentChartPalette


class InvestmentDistributionBuilder:
    """Serialises ``(label, amount, share)`` triples adding a hex color per slice."""

    @classmethod
    def build(
        cls,
        analytics: InvestmentPortfolioAnalytics,
        currency_code: str,
    ) -> list[dict]:
        """Return one dict per slice, ordered as returned by analytics."""
        rows = analytics.category_distribution_for(currency_code)
        return [cls._row_to_dict(index, row) for index, row in enumerate(rows)]

    @classmethod
    def _row_to_dict(cls, index: int, row: tuple[str, float, float]) -> dict:
        label, amount, share = row
        return {
            "caption": label,
            "amount": amount,
            "share_ratio": share,
            "color": InvestmentChartPalette.color_at(index),
        }
