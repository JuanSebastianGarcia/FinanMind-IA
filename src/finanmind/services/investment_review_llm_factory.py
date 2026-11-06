"""Builds the active LLM client for the investment review pipeline."""

from __future__ import annotations

from finanmind.services.budget_ai_provider import BudgetAiProvider
from finanmind.services.budget_ai_provider_store import BudgetAiProviderStore
from finanmind.services.budget_review_llm_port import BudgetReviewLlmPort
from finanmind.services.claude_cli_chat_client import ClaudeCliChatClient
from finanmind.services.claude_cli_locator import ClaudeCliLocator
from finanmind.services.claude_cli_model_store import ClaudeCliModelStore
from finanmind.services.investment_ai_engine import InvestmentAiEngine
from finanmind.services.investment_ai_engine_store import InvestmentAiEngineStore
from finanmind.services.llm_configuration_error import LlmConfigurationError
from finanmind.services.llm_http_chat_client import LlmHttpChatClient
from finanmind.services.mistral_api_key_store import MistralApiKeyStore
from finanmind.services.mistral_api_settings import MistralApiSettings
from finanmind.services.mistral_model_store import MistralModelStore
from finanmind.services.openai_api_key_store import OpenAiApiKeyStore
from finanmind.services.openai_api_settings import OpenAiApiSettings
from finanmind.services.openai_model_store import OpenAiModelStore


class InvestmentReviewLlmFactory:
    """Selects the engine (Claude Code CLI, or OpenAI/Mistral over HTTP) for reviews."""

    _OPENAI_MISSING = (
        "Falta API key de OpenAI. Configúrala en 'Configurar IA', OPENAI_API_KEY "
        "o archivo openai_api_key.txt."
    )
    _MISTRAL_MISSING = (
        "Falta API key de Mistral. Configúrala en 'Configurar IA', MISTRAL_API_KEY "
        "o archivo mistral_api_key.txt."
    )

    _CLAUDE_CLI_MISSING = (
        "No se encontró Claude Code (CLI). Instálalo o define FINANMIND_CLAUDE_CLI_PATH "
        "con la ruta a claude.exe."
    )

    @classmethod
    def build(cls) -> BudgetReviewLlmPort:
        """Return a client wired to the user-selected engine, vendor and model."""
        if InvestmentAiEngineStore.resolve() == InvestmentAiEngine.CLAUDE_CLI:
            return cls._claude_cli_branch()
        vendor = BudgetAiProviderStore.resolve()
        if vendor == BudgetAiProvider.MISTRAL:
            return cls._mistral_branch()
        return cls._openai_branch()

    @classmethod
    def _claude_cli_branch(cls) -> ClaudeCliChatClient:
        executable = cls._require_key(ClaudeCliLocator.locate(), cls._CLAUDE_CLI_MISSING)
        return ClaudeCliChatClient(executable=executable, model_id=ClaudeCliModelStore.resolve_model())

    @classmethod
    def _openai_branch(cls) -> LlmHttpChatClient:
        raw = cls._require_key(OpenAiApiKeyStore.resolve_key(), cls._OPENAI_MISSING)
        return LlmHttpChatClient(
            api_key=raw,
            model_id=OpenAiModelStore.resolve_model(),
            endpoint_url=OpenAiApiSettings.ENDPOINT_URL,
            vendor_label="OpenAI",
        )

    @classmethod
    def _mistral_branch(cls) -> LlmHttpChatClient:
        raw = cls._require_key(MistralApiKeyStore.resolve_key(), cls._MISTRAL_MISSING)
        return LlmHttpChatClient(
            api_key=raw,
            model_id=MistralModelStore.resolve_model(),
            endpoint_url=MistralApiSettings.ENDPOINT_URL,
            vendor_label="Mistral",
        )

    @classmethod
    def _require_key(cls, token: str | None, failure: str) -> str:
        if not token:
            raise LlmConfigurationError(failure)
        return token
