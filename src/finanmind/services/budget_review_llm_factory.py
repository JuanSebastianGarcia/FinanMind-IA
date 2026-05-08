"""Builds the active LLM client from persisted provider + key + model stores."""

from __future__ import annotations

from finanmind.services.budget_ai_provider import BudgetAiProvider
from finanmind.services.budget_ai_provider_store import BudgetAiProviderStore
from finanmind.services.budget_review_llm_port import BudgetReviewLlmPort
from finanmind.services.llm_configuration_error import LlmConfigurationError
from finanmind.services.llm_http_chat_client import LlmHttpChatClient
from finanmind.services.mistral_api_key_store import MistralApiKeyStore
from finanmind.services.mistral_api_settings import MistralApiSettings
from finanmind.services.mistral_model_store import MistralModelStore
from finanmind.services.openai_api_key_store import OpenAiApiKeyStore
from finanmind.services.openai_api_settings import OpenAiApiSettings
from finanmind.services.openai_model_store import OpenAiModelStore


class BudgetReviewLlmFactory:
    """Selects vendor (OpenAI vs Mistral) and returns a configured HTTP client."""

    _OPENAI_MISSING = (
        "Falta API key de OpenAI. Configúrala en 'Configurar IA', OPENAI_API_KEY "
        "o archivo openai_api_key.txt."
    )
    _MISTRAL_MISSING = (
        "Falta API key de Mistral. Configúrala en 'Configurar IA', MISTRAL_API_KEY "
        "o archivo mistral_api_key.txt."
    )

    @classmethod
    def build(cls) -> BudgetReviewLlmPort:
        vendor = BudgetAiProviderStore.resolve()
        if vendor == BudgetAiProvider.MISTRAL:
            return cls._mistral_branch()
        return cls._openai_branch()

    @classmethod
    def _openai_branch(cls) -> LlmHttpChatClient:
        raw = cls._require_key(OpenAiApiKeyStore.resolve_key(), cls._OPENAI_MISSING)
        return cls._openai_http(raw)

    @classmethod
    def _mistral_branch(cls) -> LlmHttpChatClient:
        raw = cls._require_key(MistralApiKeyStore.resolve_key(), cls._MISTRAL_MISSING)
        return cls._mistral_http(raw)

    @classmethod
    def _openai_http(cls, token: str) -> LlmHttpChatClient:
        return LlmHttpChatClient(
            api_key=token,
            model_id=OpenAiModelStore.resolve_model(),
            endpoint_url=OpenAiApiSettings.ENDPOINT_URL,
            vendor_label="OpenAI",
        )

    @classmethod
    def _mistral_http(cls, token: str) -> LlmHttpChatClient:
        return LlmHttpChatClient(
            api_key=token,
            model_id=MistralModelStore.resolve_model(),
            endpoint_url=MistralApiSettings.ENDPOINT_URL,
            vendor_label="Mistral",
        )

    @classmethod
    def _require_key(cls, token: str | None, failure: str) -> str:
        if not token:
            raise LlmConfigurationError(failure)
        return token
