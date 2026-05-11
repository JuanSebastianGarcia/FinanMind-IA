"""Single bullet returned by the AI investment review (title + detail)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class InvestmentReviewNote:
    """Reusable shape for decisions, ideas, and proposed portfolio changes."""

    title: str
    detail: str

    def cleaned_title(self) -> str:
        """Return the title trimmed of surrounding whitespace."""
        return self.title.strip()

    def cleaned_detail(self) -> str:
        """Return the detail trimmed of surrounding whitespace."""
        return self.detail.strip()
