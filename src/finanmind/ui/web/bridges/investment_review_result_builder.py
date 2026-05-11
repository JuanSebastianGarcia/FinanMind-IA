"""Serialises an ``InvestmentReviewResult`` for the AI review JS panel."""

from __future__ import annotations

from finanmind.models.investment_review_result import InvestmentReviewResult
from finanmind.ui.web.bridges.investment_review_note_serializer import (
    InvestmentReviewNoteSerializer,
)


class InvestmentReviewResultBuilder:
    """Maps the dataclass result into a flat dict ready for JSON transport."""

    @classmethod
    def build(cls, result: InvestmentReviewResult) -> dict:
        """Return the full review payload (summary, risk, sections, research)."""
        return {
            "summary": result.summary.strip(),
            "risk_level": result.risk_level.value,
            "decisions": InvestmentReviewNoteSerializer.many(result.decisions),
            "ideas": InvestmentReviewNoteSerializer.many(result.ideas),
            "portfolio_changes": InvestmentReviewNoteSerializer.many(result.portfolio_changes),
            "research_notes": cls._clean_research(result.research_notes),
        }

    @classmethod
    def _clean_research(cls, raw: list[str]) -> list[str]:
        return [item.strip() for item in raw if item and item.strip()]
