"""Serializes the LLM settings dialog state (provider, key, model, env locks)."""

from __future__ import annotations

from finanmind.services.budget_ai_provider_store import BudgetAiProviderStore
from finanmind.services.mistral_api_key_store import MistralApiKeyStore
from finanmind.services.mistral_api_settings import MistralApiSettings
from finanmind.services.mistral_model_store import MistralModelStore
from finanmind.services.openai_api_key_store import OpenAiApiKeyStore
from finanmind.services.openai_api_settings import OpenAiApiSettings
from finanmind.services.openai_model_store import OpenAiModelStore


class LlmSettingsPayloadBuilder:
    """Returns the full snapshot of credentials/models for both vendors."""

    @classmethod
    def build(cls) -> dict:
        """Return active provider plus per-vendor key, model and env locks."""
        return {
            "active_provider": BudgetAiProviderStore.resolve().value,
            "provider_env_locked": BudgetAiProviderStore.env_var_in_use(),
            "openai": cls._openai_block(),
            "mistral": cls._mistral_block(),
        }

    @classmethod
    def _openai_block(cls) -> dict:
        return {
            "api_key": OpenAiApiKeyStore.resolve_key() or "",
            "api_key_env_locked": OpenAiApiKeyStore.env_var_in_use(),
            "model_id": OpenAiModelStore.resolve_model(),
            "model_env_locked": OpenAiModelStore.env_var_in_use(),
            "default_model_id": OpenAiApiSettings.DEFAULT_MODEL_ID,
        }

    @classmethod
    def _mistral_block(cls) -> dict:
        return {
            "api_key": MistralApiKeyStore.resolve_key() or "",
            "api_key_env_locked": MistralApiKeyStore.env_var_in_use(),
            "model_id": MistralModelStore.resolve_model(),
            "model_env_locked": MistralModelStore.env_var_in_use(),
            "default_model_id": MistralApiSettings.DEFAULT_MODEL_ID,
        }
