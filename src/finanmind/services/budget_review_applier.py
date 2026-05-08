"""Applies accepted AI recommendations to the live budget workspace."""

from __future__ import annotations

import logging

from finanmind.budget.book_service import BudgetBookService
from finanmind.models.budget_review_recommendation import BudgetReviewRecommendation


class BudgetReviewApplier:
    """Maps recommendations onto BudgetBookService.update_label calls."""

    def __init__(self, book: BudgetBookService) -> None:
        self._book = book
        self._log = logging.getLogger("finanmind.review")

    def apply(self, recommendations: list[BudgetReviewRecommendation]) -> int:
        """Apply each recommendation; returns how many labels were changed."""
        if not recommendations:
            return 0
        changed = 0
        for rec in recommendations:
            if self._apply_one(rec):
                changed += 1
        return changed

    def _apply_one(self, rec: BudgetReviewRecommendation) -> bool:
        category_id = self._find_category_id(rec.label_id)
        if category_id is None:
            self._log.warning("Skipping unknown label_id=%s", rec.label_id)
            return False
        try:
            self._book.update_label(category_id, rec.label_id, rec.label_title, rec.suggested_amount_cop)
        except (ValueError, KeyError) as exc:
            self._log.warning("Failed to apply rec on %s: %s", rec.label_id, exc)
            return False
        return True

    def _find_category_id(self, label_id: str) -> str | None:
        for cat in self._book.peek().categories:
            for lbl in cat.labels:
                if lbl.label_id == label_id:
                    return cat.category_id
        return None
