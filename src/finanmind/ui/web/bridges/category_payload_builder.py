"""Serialises ``BudgetCategory`` instances (with their labels) for the UI."""

from __future__ import annotations

from finanmind.budget.salary_shares import BudgetSalaryShares
from finanmind.models.budget_category import BudgetCategory
from finanmind.services.credit_card_service import CreditCardService
from finanmind.ui.web.bridges.label_payload_builder import LabelPayloadBuilder


class CategoryPayloadBuilder:
    """Maps each category to a JSON dict including precomputed percentages."""

    @classmethod
    def build_many(
        cls,
        categories: list[BudgetCategory],
        salary: float,
        cards: CreditCardService | None,
    ) -> list[dict]:
        """Build payloads for every category in display order."""
        shares = cls._shares_map(categories, salary)
        out: list[dict] = []
        for cat in categories:
            pct = shares.get(cat.category_id, 0.0)
            out.append(cls._build_one(cat, pct, salary, cards))
        return out

    @classmethod
    def _shares_map(cls, categories: list[BudgetCategory], salary: float) -> dict[str, float]:
        pairs = [(c.category_id, [lbl.amount_cop for lbl in c.labels]) for c in categories]
        return BudgetSalaryShares.map_by_category(salary, pairs)

    @classmethod
    def _build_one(
        cls,
        cat: BudgetCategory,
        percent: float,
        salary: float,
        cards: CreditCardService | None,
    ) -> dict:
        labels = LabelPayloadBuilder.build_many(cat.labels, salary, cards)
        total = sum(lbl.amount_cop for lbl in cat.labels)
        return {
            "id": cat.category_id,
            "title": cat.title,
            "color": cls._resolve_color(cat),
            "percent_of_salary": percent,
            "total_cop": total,
            "labels": labels,
        }

    @classmethod
    def _resolve_color(cls, cat: BudgetCategory) -> str:
        return cat.color_dark.strip() or cat.color_light.strip()
