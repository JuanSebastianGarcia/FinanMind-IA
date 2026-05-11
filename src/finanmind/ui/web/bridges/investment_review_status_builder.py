"""Builds the idle status payload shown above the AI review actions."""

from __future__ import annotations

from finanmind.services.budget_ai_provider import BudgetAiProvider
from finanmind.services.budget_ai_provider_store import BudgetAiProviderStore
from finanmind.services.mistral_model_store import MistralModelStore
from finanmind.services.openai_model_store import OpenAiModelStore


class InvestmentReviewStatusBuilder:
    """Resolves the active vendor + model for the AI status label."""

    @classmethod
    def build(cls) -> dict:
        """Return a flat dict with vendor name and model slug for the UI."""
        return {"vendor": cls._vendor_human_name(), "model": cls._active_model_slug()}

    @classmethod
    def _vendor_human_name(cls) -> str:
        if BudgetAiProviderStore.resolve() == BudgetAiProvider.MISTRAL:
            return "Mistral"
        return "OpenAI"

    @classmethod
    def _active_model_slug(cls) -> str:
        if BudgetAiProviderStore.resolve() == BudgetAiProvider.MISTRAL:
            return MistralModelStore.resolve_model()
        return OpenAiModelStore.resolve_model()
