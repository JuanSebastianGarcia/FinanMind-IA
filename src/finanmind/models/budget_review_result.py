"""Full AI-generated review of a budget snapshot."""

from __future__ import annotations

from dataclasses import dataclass, field

from finanmind.models.budget_review_recommendation import BudgetReviewRecommendation
from finanmind.models.budget_review_risk import BudgetReviewRiskLevel


@dataclass
class BudgetReviewResult:
    """Top-level container with summary, items, projected savings, risk."""

    summary: str
    recommendations: list[BudgetReviewRecommendation] = field(default_factory=list)
    projected_savings_cop: float = 0.0
    risk_level: BudgetReviewRiskLevel = BudgetReviewRiskLevel.MEDIUM

    def has_changes(self) -> bool:
        """True when at least one recommendation alters an amount."""
        return any(abs(r.delta_cop) > 0.5 for r in self.recommendations)
