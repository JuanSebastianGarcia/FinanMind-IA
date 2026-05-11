"""Serialises ``BudgetLabel`` instances (plus credit-card link captions) for the UI."""

from __future__ import annotations

from finanmind.budget.salary_shares import BudgetSalaryShares
from finanmind.models.budget_label import BudgetLabel
from finanmind.services.credit_card_service import CreditCardService


class LabelPayloadBuilder:
    """Maps budget labels into JSON dicts the front-end can render directly."""

    @classmethod
    def build_many(
        cls,
        labels: list[BudgetLabel],
        salary: float,
        cards: CreditCardService | None,
    ) -> list[dict]:
        """Build payloads for every label inside one category."""
        return [cls._build_one(lbl, salary, cards) for lbl in labels]

    @classmethod
    def _build_one(cls, label: BudgetLabel, salary: float, cards: CreditCardService | None) -> dict:
        share = BudgetSalaryShares.amount_share_percent(salary, label.amount_cop)
        return {
            "id": label.label_id,
            "title": label.title,
            "amount_cop": label.amount_cop,
            "percent_of_salary": share,
            "link_caption": cls._link_caption(label.label_id, cards),
            "linked_cc_category_id": cls._linked_id(label.label_id, cards),
        }

    @classmethod
    def _link_caption(cls, label_id: str, cards: CreditCardService | None) -> str:
        if cards is None:
            return ""
        cat = cards.category_for_label(label_id)
        if cat is None:
            return ""
        card = cards.card_for_category(cat.category_id)
        if card is None:
            return f"↪ Tarjeta · {cat.title}"
        return f"↪ {card.name} · {cat.title}"

    @classmethod
    def _linked_id(cls, label_id: str, cards: CreditCardService | None) -> str:
        if cards is None:
            return ""
        cat = cards.category_for_label(label_id)
        return cat.category_id if cat is not None else ""
