"""Error raised when the AI investment review payload is malformed."""

from __future__ import annotations


class InvestmentReviewResponseError(ValueError):
    """Raised when the AI payload does not match the expected schema."""
