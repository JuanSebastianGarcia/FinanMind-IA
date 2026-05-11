"""Resolves the active AI vendor + model for the Budget review header strip."""

from __future__ import annotations

from finanmind.services.budget_ai_provider import BudgetAiProvider
from finanmind.services.budget_ai_provider_store import BudgetAiProviderStore
from finanmind.services.mistral_model_store import MistralModelStore
from finanmind.services.openai_model_store import OpenAiModelStore


class BudgetReviewStatusBuilder:
    """Mirrors the Tk idle status by returning vendor name and model slug."""

    @classmethod
    def build(cls) -> dict:
        """Return a flat dict with vendor name, model slug and env-lock flag."""
        return {
            "vendor": cls._vendor_human_name(),
            "model": cls._active_model_slug(),
            "provider_env_locked": BudgetAiProviderStore.env_var_in_use(),
        }

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
