"""High-level adapter for the AI investment review (rules, status, analyze)."""

from __future__ import annotations

from finanmind.models.investment_review_request import InvestmentReviewRequest
from finanmind.services.investment_review_llm_factory import InvestmentReviewLlmFactory
from finanmind.services.investment_review_rules_store import (
    InvestmentReviewRulesStore,
)
from finanmind.services.investment_review_service import InvestmentReviewService
from finanmind.services.investment_review_service_error import (
    InvestmentReviewServiceError,
)
from finanmind.services.investment_service import InvestmentService
from finanmind.services.llm_configuration_error import LlmConfigurationError
from finanmind.services.usd_cop_rate_store import UsdCopRateStore
from finanmind.ui.web.bridges.investment_review_result_builder import (
    InvestmentReviewResultBuilder,
)
from finanmind.ui.web.bridges.investment_review_rules_builder import (
    InvestmentReviewRulesBuilder,
)
from finanmind.ui.web.bridges.investment_review_status_builder import (
    InvestmentReviewStatusBuilder,
)


class InvestmentReviewBridge:
    """Exposes AI review actions and the personal rules CRUD to JavaScript."""

    def __init__(
        self,
        service: InvestmentService,
        rules_store: InvestmentReviewRulesStore,
    ) -> None:
        self._service = service
        self._rules = rules_store

    def get_setup(self) -> dict:
        """Return rules, current rate, AI status, and credentials readiness."""
        return {
            "rules": InvestmentReviewRulesBuilder.build(self._rules),
            "rate": UsdCopRateStore.resolve_rate(),
            "rate_env_locked": UsdCopRateStore.env_var_in_use(),
            "status": InvestmentReviewStatusBuilder.build(),
            "credentials_ready": self._credentials_ready(),
        }

    def add_rule(self, text: str) -> list[dict]:
        """Append a new personal rule and return the refreshed rules list."""
        self._rules.add(text)
        return InvestmentReviewRulesBuilder.build(self._rules)

    def update_rule(self, rule_id: str, text: str) -> list[dict]:
        """Edit an existing rule and return the refreshed rules list."""
        self._rules.update(rule_id, text)
        return InvestmentReviewRulesBuilder.build(self._rules)

    def delete_rule(self, rule_id: str) -> list[dict]:
        """Remove one rule and return the refreshed rules list."""
        self._rules.delete(rule_id)
        return InvestmentReviewRulesBuilder.build(self._rules)

    def analyze(self, rate: float) -> dict:
        """Persist the rate, call the model, and return the review payload."""
        self._require_entries()
        rate_value = self._coerce_rate(rate)
        self._persist_rate_quietly(rate_value)
        result = self._run_review(rate_value)
        return InvestmentReviewResultBuilder.build(result)

    def _require_entries(self) -> None:
        if not self._service.entries_snapshot():
            raise ValueError("Registra al menos una inversión antes de pedir un análisis.")

    def _coerce_rate(self, raw: float) -> float:
        try:
            value = float(raw)
        except (TypeError, ValueError) as exc:
            raise ValueError("La tasa USD→COP debe ser un número.") from exc
        if value <= 0:
            raise ValueError("La tasa USD→COP debe ser mayor que cero.")
        return value

    def _persist_rate_quietly(self, value: float) -> None:
        if UsdCopRateStore.env_var_in_use():
            return
        try:
            UsdCopRateStore.persist_rate(value)
        except (RuntimeError, ValueError):
            return

    def _run_review(self, rate: float):
        request = self._build_request(rate)
        backend = InvestmentReviewLlmFactory.build()
        engine = InvestmentReviewService(client=backend)
        return engine.run_review(request)

    def _build_request(self, rate: float) -> InvestmentReviewRequest:
        return InvestmentReviewRequest(
            entries=self._service.entries_snapshot(),
            categories=self._service.categories_snapshot(),
            usd_to_cop_rate=rate,
            personal_rules=self._collect_rule_texts(),
        )

    def _collect_rule_texts(self) -> list[str]:
        return [rule.cleaned_text() for rule in self._rules.snapshot()]

    def _credentials_ready(self) -> bool:
        try:
            InvestmentReviewLlmFactory.build()
            return True
        except LlmConfigurationError:
            return False
        except (RuntimeError, ValueError):
            return False
