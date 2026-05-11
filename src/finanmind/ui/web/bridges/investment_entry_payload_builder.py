"""Serialises one investment holding (one card row in the list)."""

from __future__ import annotations

from finanmind.models.investment_entry import InvestmentEntry
from finanmind.services.investment_portfolio_analytics import InvestmentPortfolioAnalytics


class InvestmentEntryPayloadBuilder:
    """Produces a JSON dict for a single ``InvestmentEntry``."""

    @classmethod
    def build(cls, entry: InvestmentEntry, analytics: InvestmentPortfolioAnalytics) -> dict:
        """Return the row payload with category caption and currency share."""
        return {
            "investment_id": entry.investment_id,
            "category_id": entry.category_id,
            "category_caption": analytics.category_label_for(entry.category_id),
            "amount": entry.amount,
            "currency_code": entry.currency_code.upper(),
            "invested_date_iso": entry.invested_date_iso,
            "description": entry.description,
            "share_ratio": analytics.share_for_entry(entry),
        }
