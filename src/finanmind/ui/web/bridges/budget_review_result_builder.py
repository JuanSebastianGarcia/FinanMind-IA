"""Aggregates a ``BudgetReviewResult`` into a JSON payload for the front-end."""

from __future__ import annotations

from finanmind.models.budget_review_result import BudgetReviewResult
from finanmind.ui.web.bridges.budget_review_recommendation_serializer import (
    BudgetReviewRecommendationSerializer,
)


class BudgetReviewResultBuilder:
    """Serialises summary, recommendations, projected savings and risk level."""

    @classmethod
    def build(cls, result: BudgetReviewResult) -> dict:
        """Return the full review snapshot consumed by the web UI."""
        return {
            "summary": result.summary,
            "projected_savings_cop": result.projected_savings_cop,
            "risk_level": result.risk_level.value,
            "has_changes": result.has_changes(),
            "recommendations": cls._build_recommendations(result),
        }

    @classmethod
    def _build_recommendations(cls, result: BudgetReviewResult) -> list[dict]:
        return [BudgetReviewRecommendationSerializer.build(rec) for rec in result.recommendations]
