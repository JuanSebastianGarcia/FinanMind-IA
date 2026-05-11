"""One user-defined personal rule sent alongside the investment review."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class InvestmentReviewRule:
    """Free-form note (preference, life situation, intent) the AI must respect."""

    rule_id: str
    text: str

    def cleaned_text(self) -> str:
        """Return the rule body trimmed of surrounding whitespace."""
        return self.text.strip()

    def is_blank(self) -> bool:
        """True when the rule is effectively empty after trimming."""
        return self.cleaned_text() == ""
