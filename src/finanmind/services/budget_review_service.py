"""High-level orchestrator that runs an AI budget review end-to-end."""

from __future__ import annotations

import logging

from finanmind.models.budget_review_request import BudgetReviewRequest
from finanmind.models.budget_review_result import BudgetReviewResult
from finanmind.services.budget_review_llm_port import BudgetReviewLlmPort
from finanmind.services.budget_review_prompt_builder import BudgetReviewPromptBuilder
from finanmind.services.budget_review_response_parser import (
    BudgetReviewResponseError,
    BudgetReviewResponseParser,
)
from finanmind.services.llm_chat_completion_error import LlmChatCompletionError


class BudgetReviewServiceError(Exception):
    """Wraps any failure during the review pipeline (network, parse, etc.)."""


class BudgetReviewService:
    """Bridges the prompt builder, an HTTP LLM client, and the JSON parser."""

    def __init__(self, client: BudgetReviewLlmPort) -> None:
        self._client = client
        self._log = logging.getLogger("finanmind.review")

    def run_review(self, request: BudgetReviewRequest) -> BudgetReviewResult:
        """Execute the review and return a typed result."""
        self._log_invocation(request)
        raw_json = self._call_model(request)
        self._log.debug("AI raw payload bytes=%d", len(raw_json))
        return self._parse_payload(raw_json, request)

    def _log_invocation(self, request: BudgetReviewRequest) -> None:
        salary = request.workspace.salary_cop
        cats = len(request.workspace.categories)
        ctx_len = len(request.cleaned_context())
        self._log.info("Review run: salary=%s cats=%s context_len=%s", salary, cats, ctx_len)

    def _call_model(self, request: BudgetReviewRequest) -> str:
        system_prompt = BudgetReviewPromptBuilder.build_system_prompt()
        user_prompt = BudgetReviewPromptBuilder.build_user_prompt(request)
        try:
            return self._client.request_json_completion(system_prompt, user_prompt)
        except LlmChatCompletionError as exc:
            self._log.error("LLM failure: %s", exc)
            raise BudgetReviewServiceError(str(exc)) from exc

    def _parse_payload(self, raw_json: str, request: BudgetReviewRequest) -> BudgetReviewResult:
        try:
            return BudgetReviewResponseParser.parse(raw_json, request.workspace)
        except BudgetReviewResponseError as exc:
            self._log.error("Parse failure: %s | raw=%s", exc, raw_json[:400])
            raise BudgetReviewServiceError(str(exc)) from exc
