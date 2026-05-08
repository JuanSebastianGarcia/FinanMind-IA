"""One AI-suggested change for a single budget label."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BudgetReviewRecommendation:
    """Mapping between an existing label and its proposed new amount."""

    label_id: str
    category_title: str
    label_title: str
    current_amount_cop: float
    suggested_amount_cop: float
    reason: str

    @property
    def delta_cop(self) -> float:
        """Difference between suggestion and current amount (positive = increase)."""
        return self.suggested_amount_cop - self.current_amount_cop
