"""Serialises personal investment review rules for the JavaScript layer."""

from __future__ import annotations

from finanmind.services.investment_review_rules_store import (
    InvestmentReviewRulesStore,
)


class InvestmentReviewRulesBuilder:
    """Turns the persisted rules list into a JSON-friendly payload."""

    @classmethod
    def build(cls, store: InvestmentReviewRulesStore) -> list[dict]:
        """Return one dict per rule with its id and trimmed text body."""
        return [{"rule_id": r.rule_id, "text": r.cleaned_text()} for r in store.snapshot()]
