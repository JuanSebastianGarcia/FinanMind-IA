"""Aggregates the entire budget snapshot the front-end needs to render the panel."""

from __future__ import annotations

from finanmind.models.budget_workspace import BudgetWorkspace
from finanmind.services.credit_card_service import CreditCardService
from finanmind.ui.web.bridges.category_payload_builder import CategoryPayloadBuilder
from finanmind.ui.web.bridges.salary_summary_builder import SalarySummaryBuilder


class BudgetPayloadBuilder:
    """Produces the full budget state payload exposed to JavaScript."""

    @classmethod
    def build(cls, workspace: BudgetWorkspace, cards: CreditCardService | None) -> dict:
        """Return salary summary plus serialised categories."""
        salary = workspace.salary_cop
        return {
            "salary_cop": salary,
            "summary": SalarySummaryBuilder.build(workspace),
            "categories": CategoryPayloadBuilder.build_many(workspace.categories, salary, cards),
        }
