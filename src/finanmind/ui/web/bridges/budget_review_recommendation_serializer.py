"""Serializes one ``BudgetReviewRecommendation`` for the web review dialog."""

from __future__ import annotations

from finanmind.models.budget_review_recommendation import BudgetReviewRecommendation


class BudgetReviewRecommendationSerializer:
    """Converts a recommendation dataclass into a JSON-friendly dict."""

    @classmethod
    def build(cls, rec: BudgetReviewRecommendation) -> dict:
        """Return label paths, current vs suggested amounts, delta, and reason."""
        return {
            "label_id": rec.label_id,
            "category_title": rec.category_title,
            "label_title": rec.label_title,
            "current_amount_cop": rec.current_amount_cop,
            "suggested_amount_cop": rec.suggested_amount_cop,
            "delta_cop": rec.delta_cop,
            "reason": rec.reason,
        }
