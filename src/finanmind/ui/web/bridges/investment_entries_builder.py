"""Builds the ordered list of investment row payloads (newest first)."""

from __future__ import annotations

from finanmind.models.investment_entry import InvestmentEntry
from finanmind.services.investment_portfolio_analytics import InvestmentPortfolioAnalytics
from finanmind.ui.web.bridges.investment_entry_payload_builder import (
    InvestmentEntryPayloadBuilder,
)


class InvestmentEntriesBuilder:
    """Sorts entries by date desc (then category) and turns each into a dict."""

    @classmethod
    def build(
        cls,
        entries: list[InvestmentEntry],
        analytics: InvestmentPortfolioAnalytics,
    ) -> list[dict]:
        """Return the list of row payloads ordered for the UI."""
        ordered = cls._ordered_entries(entries)
        return [InvestmentEntryPayloadBuilder.build(ent, analytics) for ent in ordered]

    @classmethod
    def _ordered_entries(cls, entries: list[InvestmentEntry]) -> list[InvestmentEntry]:
        return sorted(
            entries,
            key=lambda e: (e.invested_date_iso, e.category_id.lower()),
            reverse=True,
        )
