"""Full AI-generated review of an investment portfolio snapshot."""

from __future__ import annotations

from dataclasses import dataclass, field

from finanmind.models.investment_review_note import InvestmentReviewNote
from finanmind.models.investment_review_risk import InvestmentReviewRiskLevel


@dataclass
class InvestmentReviewResult:
    """Typed envelope rendered in the investments UI after a successful call."""

    summary: str
    decisions: list[InvestmentReviewNote] = field(default_factory=list)
    ideas: list[InvestmentReviewNote] = field(default_factory=list)
    portfolio_changes: list[InvestmentReviewNote] = field(default_factory=list)
    research_notes: list[str] = field(default_factory=list)
    risk_level: InvestmentReviewRiskLevel = InvestmentReviewRiskLevel.MEDIUM

    def has_any_recommendation(self) -> bool:
        """True when at least one bullet was returned in any section."""
        return bool(self.decisions or self.ideas or self.portfolio_changes)
