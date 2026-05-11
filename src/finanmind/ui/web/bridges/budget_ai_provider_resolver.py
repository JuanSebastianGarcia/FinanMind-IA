"""Maps the loose provider token coming from JS to the typed enum value."""

from __future__ import annotations

from finanmind.services.budget_ai_provider import BudgetAiProvider


class BudgetAiProviderResolver:
    """Converts a free-form string into a ``BudgetAiProvider`` enum entry."""

    @classmethod
    def from_token(cls, raw: str) -> BudgetAiProvider:
        """Return ``MISTRAL`` only when the token matches; defaults to OPENAI."""
        token = (raw or "").strip().lower()
        if token == BudgetAiProvider.MISTRAL.value:
            return BudgetAiProvider.MISTRAL
        return BudgetAiProvider.OPENAI
