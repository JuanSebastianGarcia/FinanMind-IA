"""High-level orchestrator that runs an AI investment review end-to-end."""

from __future__ import annotations

import logging

from finanmind.models.investment_review_request import InvestmentReviewRequest
from finanmind.models.investment_review_result import InvestmentReviewResult
from finanmind.services.budget_review_llm_port import BudgetReviewLlmPort
from finanmind.services.investment_review_prompt_builder import (
    InvestmentReviewPromptBuilder,
)
from finanmind.services.investment_review_response_error import (
    InvestmentReviewResponseError,
)
from finanmind.services.investment_review_response_parser import (
    InvestmentReviewResponseParser,
)
from finanmind.services.investment_review_service_error import (
    InvestmentReviewServiceError,
)
from finanmind.services.llm_chat_completion_error import LlmChatCompletionError


class InvestmentReviewService:
    """Bridges the prompt builder, an HTTP LLM client, and the JSON parser."""

    def __init__(self, client: BudgetReviewLlmPort) -> None:
        self._client = client
        self._log = logging.getLogger("finanmind.investments.review")

    def run_review(self, request: InvestmentReviewRequest) -> InvestmentReviewResult:
        """Execute the review and return a typed result."""
        self._log_invocation(request)
        raw_json = self._call_model(request)
        self._log.debug("AI raw payload bytes=%d", len(raw_json))
        return self._parse_payload(raw_json)

    def _log_invocation(self, request: InvestmentReviewRequest) -> None:
        entries = request.entry_count()
        cats = request.category_count()
        self._log.info("Investment review run: entries=%s categories=%s", entries, cats)

    def _call_model(self, request: InvestmentReviewRequest) -> str:
        system_prompt = InvestmentReviewPromptBuilder.build_system_prompt()
        user_prompt = InvestmentReviewPromptBuilder.build_user_prompt(request)
        try:
            return self._client.request_json_completion(system_prompt, user_prompt)
        except LlmChatCompletionError as exc:
            self._log.error("LLM failure: %s", exc)
            raise InvestmentReviewServiceError(str(exc)) from exc

    def _parse_payload(self, raw_json: str) -> InvestmentReviewResult:
        try:
            return InvestmentReviewResponseParser.parse(raw_json)
        except InvestmentReviewResponseError as exc:
            self._log.error("Parse failure: %s | raw=%s", exc, raw_json[:400])
            raise InvestmentReviewServiceError(str(exc)) from exc
