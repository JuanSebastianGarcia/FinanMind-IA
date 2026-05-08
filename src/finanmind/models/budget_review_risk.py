"""Risk-level vocabulary used by AI budget reviews."""

from __future__ import annotations

from enum import Enum


class BudgetReviewRiskLevel(str, Enum):
    """Discrete risk buckets the model is allowed to return."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    @classmethod
    def parse(cls, raw: str) -> "BudgetReviewRiskLevel":
        """Map a free-form string to a known level (defaults to MEDIUM)."""
        token = (raw or "").strip().lower()
        for level in cls:
            if level.value == token:
                return level
        return cls.MEDIUM
