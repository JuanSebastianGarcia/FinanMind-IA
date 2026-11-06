"""Builds the idle status payload shown above the AI review actions."""

from __future__ import annotations

from finanmind.services.budget_ai_provider import BudgetAiProvider
from finanmind.services.budget_ai_provider_store import BudgetAiProviderStore
from finanmind.services.claude_cli_model_store import ClaudeCliModelStore
from finanmind.services.investment_ai_engine import InvestmentAiEngine
from finanmind.services.investment_ai_engine_store import InvestmentAiEngineStore
from finanmind.services.mistral_model_store import MistralModelStore
from finanmind.services.openai_model_store import OpenAiModelStore


class InvestmentReviewStatusBuilder:
    """Resolves the active engine/vendor + model for the AI status label."""

    _CLI_DEFAULT_MODEL_LABEL = "predeterminado de Claude Code"

    @classmethod
    def build(cls) -> dict:
        """Return a flat dict with vendor name and model slug for the UI."""
        if InvestmentAiEngineStore.resolve() == InvestmentAiEngine.CLAUDE_CLI:
            model = ClaudeCliModelStore.resolve_model() or cls._CLI_DEFAULT_MODEL_LABEL
            return {"vendor": "Claude Code (CLI)", "model": model}
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
