"""Risk-level vocabulary used by AI investment reviews."""

from __future__ import annotations

from enum import Enum


class InvestmentReviewRiskLevel(str, Enum):
    """Discrete risk buckets the model is allowed to return for a portfolio."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    @classmethod
    def parse(cls, raw: str) -> "InvestmentReviewRiskLevel":
        """Map a free-form string to a known level (defaults to MEDIUM)."""
        token = (raw or "").strip().lower()
        for level in cls:
            if level.value == token:
                return level
        return cls.MEDIUM
