"""Serialises one ``InvestmentReviewNote`` (title + detail) as a dict."""

from __future__ import annotations

from finanmind.models.investment_review_note import InvestmentReviewNote


class InvestmentReviewNoteSerializer:
    """Pure function utility that returns clean strings ready for JSON."""

    @classmethod
    def to_dict(cls, note: InvestmentReviewNote) -> dict:
        """Return ``{"title": ..., "detail": ...}`` with trimmed strings."""
        return {"title": note.cleaned_title(), "detail": note.cleaned_detail()}

    @classmethod
    def many(cls, notes: list[InvestmentReviewNote]) -> list[dict]:
        """Map a list of notes to a list of dicts."""
        return [cls.to_dict(n) for n in notes]
