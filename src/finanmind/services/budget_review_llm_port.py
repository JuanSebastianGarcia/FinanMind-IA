"""Protocol implemented by HTTP clients consumed by BudgetReviewService."""

from __future__ import annotations

from typing import Protocol


class BudgetReviewLlmPort(Protocol):
    """Any vendor that accepts system/user prompts and returns JSON text."""

    def request_json_completion(self, system_prompt: str, user_prompt: str) -> str:
        """Return assistant message body (must be parseable JSON for our parser)."""
        ...
