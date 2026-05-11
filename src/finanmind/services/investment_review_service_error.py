"""Error wrapping failures of the investment review pipeline."""

from __future__ import annotations


class InvestmentReviewServiceError(Exception):
    """Wraps any failure during the review pipeline (network, parse, etc.)."""
