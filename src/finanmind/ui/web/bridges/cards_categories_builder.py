"""Serialises a card's expense categories with their optional budget-label link caption."""

from __future__ import annotations

from finanmind.budget.book_service import BudgetBookService
from finanmind.models.credit_card_category import CreditCardCategory
from finanmind.services.credit_card_service import CreditCardService


class CardsCategoriesBuilder:
    """Maps each expense category to its display payload (swatch + link caption)."""

    @classmethod
    def build(
        cls,
        service: CreditCardService,
        card_id: str,
        book: BudgetBookService | None,
    ) -> list[dict]:
        """Return one payload per category sorted as the service exposes them."""
        return [cls._row(cat, book) for cat in service.categories_for_card(card_id)]

    @classmethod
    def _row(cls, cat: CreditCardCategory, book: BudgetBookService | None) -> dict:
        return {
            "category_id": cat.category_id,
            "title": cat.title,
            "color": cat.color,
            "linked_label_id": cat.linked_label_id,
            "link_caption": cls._link_caption(cat.linked_label_id, book),
        }

    @classmethod
    def _link_caption(cls, label_id: str, book: BudgetBookService | None) -> str:
        path = cls._budget_label_path(label_id, book)
        if path == "":
            return ""
        return f"↪ Presupuesto · {path}"

    @classmethod
    def _budget_label_path(cls, label_id: str, book: BudgetBookService | None) -> str:
        if book is None or label_id == "":
            return ""
        for cat in book.peek().categories:
            for lbl in cat.labels:
                if lbl.label_id == label_id:
                    return f"{cat.title} → {lbl.title}"
        return ""
