"""Inputs sent to the AI before a budget review is requested."""

from __future__ import annotations

from dataclasses import dataclass

from finanmind.models.budget_workspace import BudgetWorkspace


@dataclass
class BudgetReviewRequest:
    """Pairs the user free-form context with the live workspace snapshot."""

    user_context: str
    workspace: BudgetWorkspace

    def cleaned_context(self) -> str:
        """Return the user context trimmed of surrounding whitespace."""
        return self.user_context.strip()
