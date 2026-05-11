"""Inputs sent to the AI before an investment portfolio review is requested."""

from __future__ import annotations

from dataclasses import dataclass, field

from finanmind.models.investment_category import InvestmentCategory
from finanmind.models.investment_entry import InvestmentEntry


@dataclass
class InvestmentReviewRequest:
    """Portfolio snapshot (categories + holdings) sent to the model."""

    entries: list[InvestmentEntry] = field(default_factory=list)
    categories: list[InvestmentCategory] = field(default_factory=list)
    usd_to_cop_rate: float = 4000.0
    personal_rules: list[str] = field(default_factory=list)

    def entry_count(self) -> int:
        """Return how many individual holdings are part of the snapshot."""
        return len(self.entries)

    def category_count(self) -> int:
        """Return how many declared categories are part of the snapshot."""
        return len(self.categories)

    def safe_rate(self) -> float:
        """Return a strictly positive USD→COP rate (falls back to default)."""
        if self.usd_to_cop_rate is None or self.usd_to_cop_rate <= 0:
            return 4000.0
        return float(self.usd_to_cop_rate)

    def cleaned_rules(self) -> list[str]:
        """Return personal rules trimmed and stripped of empty entries."""
        return [r.strip() for r in self.personal_rules if r and r.strip()]
