"""Flattens every budget label into ``Category → Label`` options for the link dropdown."""

from __future__ import annotations

from finanmind.budget.book_service import BudgetBookService


class CardsLabelOptionsBuilder:
    """Produces the budget-label choices used by the card-category dialog."""

    @classmethod
    def build(cls, book: BudgetBookService | None) -> list[dict]:
        """Return one option per label captioned ``Category → Label``."""
        if book is None:
            return []
        out: list[dict] = []
        for cat in book.peek().categories:
            for lbl in cat.labels:
                out.append({"caption": f"{cat.title} → {lbl.title}", "label_id": lbl.label_id})
        return out
