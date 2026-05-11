"""High-level adapter for the AI Budget review (setup, run, apply, settings)."""

from __future__ import annotations

from finanmind.budget.book_service import BudgetBookService
from finanmind.models.budget_review_recommendation import BudgetReviewRecommendation
from finanmind.models.budget_review_request import BudgetReviewRequest
from finanmind.services.budget_ai_provider import BudgetAiProvider
from finanmind.services.budget_ai_provider_store import BudgetAiProviderStore
from finanmind.services.budget_review_applier import BudgetReviewApplier
from finanmind.services.budget_review_llm_factory import BudgetReviewLlmFactory
from finanmind.services.budget_review_service import BudgetReviewService
from finanmind.services.llm_configuration_error import LlmConfigurationError
from finanmind.services.mistral_api_key_store import MistralApiKeyStore
from finanmind.services.mistral_model_store import MistralModelStore
from finanmind.services.openai_api_key_store import OpenAiApiKeyStore
from finanmind.services.openai_model_store import OpenAiModelStore
from finanmind.ui.web.bridges.budget_ai_provider_resolver import (
    BudgetAiProviderResolver,
)
from finanmind.ui.web.bridges.budget_review_result_builder import (
    BudgetReviewResultBuilder,
)
from finanmind.ui.web.bridges.budget_review_status_builder import (
    BudgetReviewStatusBuilder,
)
from finanmind.ui.web.bridges.llm_settings_payload_builder import (
    LlmSettingsPayloadBuilder,
)


class BudgetReviewBridge:
    """Exposes review actions, apply/discard and LLM credentials CRUD to JS."""

    def __init__(self, book: BudgetBookService) -> None:
        self._book = book

    def get_setup(self) -> dict:
        """Return AI status, credentials readiness and the workspace context length."""
        return {
            "status": BudgetReviewStatusBuilder.build(),
            "credentials_ready": self._credentials_ready(),
            "salary_cop": self._book.peek().salary_cop,
        }

    def set_provider(self, vendor: str) -> dict:
        """Persist the quick provider choice and return the refreshed setup."""
        if BudgetAiProviderStore.env_var_in_use():
            raise ValueError("El proveedor está fijado por la variable FINANMIND_AI_PROVIDER.")
        BudgetAiProviderStore.persist(BudgetAiProviderResolver.from_token(vendor))
        return self.get_setup()

    def run_review(self, context: str) -> dict:
        """Submit the workspace + context to the AI and return the JSON payload."""
        cleaned = (context or "").strip()
        request = BudgetReviewRequest(user_context=cleaned, workspace=self._book.peek())
        backend = BudgetReviewLlmFactory.build()
        engine = BudgetReviewService(client=backend)
        return BudgetReviewResultBuilder.build(engine.run_review(request))

    def apply_recommendations(self, payload: list[dict]) -> int:
        """Persist the accepted recommendations and return the count of changes."""
        recs = [self._payload_to_recommendation(item) for item in payload or []]
        return BudgetReviewApplier(self._book).apply(recs)

    def get_llm_settings(self) -> dict:
        """Return the per-vendor key, model and env locks for the settings dialog."""
        return LlmSettingsPayloadBuilder.build()

    def save_llm_settings(self, provider: str, api_key: str, model_id: str) -> dict:
        """Persist provider + per-vendor credentials and return the refreshed setup."""
        target = BudgetAiProviderResolver.from_token(provider)
        if not BudgetAiProviderStore.env_var_in_use():
            BudgetAiProviderStore.persist(target)
        self._persist_credentials(target, api_key or "", model_id or "")
        return self.get_setup()

    def _persist_credentials(self, provider: BudgetAiProvider, raw_key: str, raw_model: str) -> None:
        if provider == BudgetAiProvider.MISTRAL:
            self._persist_mistral(raw_key, raw_model)
            return
        self._persist_openai(raw_key, raw_model)

    def _persist_openai(self, raw_key: str, raw_model: str) -> None:
        if not OpenAiApiKeyStore.env_var_in_use() and raw_key.strip():
            OpenAiApiKeyStore.persist_key(raw_key)
        if not OpenAiModelStore.env_var_in_use():
            OpenAiModelStore.persist_model(raw_model)

    def _persist_mistral(self, raw_key: str, raw_model: str) -> None:
        if not MistralApiKeyStore.env_var_in_use() and raw_key.strip():
            MistralApiKeyStore.persist_key(raw_key)
        if not MistralModelStore.env_var_in_use():
            MistralModelStore.persist_model(raw_model)

    def _payload_to_recommendation(self, item: dict) -> BudgetReviewRecommendation:
        return BudgetReviewRecommendation(
            label_id=str(item.get("label_id", "")),
            category_title=str(item.get("category_title", "")),
            label_title=str(item.get("label_title", "")),
            current_amount_cop=float(item.get("current_amount_cop", 0) or 0),
            suggested_amount_cop=float(item.get("suggested_amount_cop", 0) or 0),
            reason=str(item.get("reason", "")),
        )

    def _credentials_ready(self) -> bool:
        try:
            BudgetReviewLlmFactory.build()
            return True
        except LlmConfigurationError:
            return False
        except (RuntimeError, ValueError):
            return False
