"""Builds the per-category bars chart shown under the expenses table."""

from __future__ import annotations

from finanmind.models.credit_card_category import CreditCardCategory
from finanmind.models.credit_card_expense import CreditCardExpense
from finanmind.services.credit_card_balance import CreditCardBalance
from finanmind.services.credit_card_service import CreditCardService


class CardsChartBuilder:
    """Aggregates expenses by category and exposes ``ratio`` for each bar."""

    _DEFAULT_COLOR = "#4f8ef7"
    _NO_CATEGORY_CAPTION = "Sin categoría"

    @classmethod
    def build(
        cls,
        service: CreditCardService,
        card_id: str,
        cycle_expenses: list[CreditCardExpense],
    ) -> list[dict]:
        """Return bars sorted by value desc, each carrying caption, ratio and color."""
        totals = CreditCardBalance.per_category_totals(cycle_expenses)
        grand = sum(totals.values())
        meta = cls._category_meta_for_card(service, card_id)
        bars = [cls._bar(cat_id, value, grand, meta) for cat_id, value in totals.items()]
        bars.sort(key=lambda b: b["amount_cop"], reverse=True)
        return bars

    @classmethod
    def _bar(cls, category_id: str, value: float, grand: float, meta: dict[str, tuple[str, str]]) -> dict:
        caption, color = meta.get(category_id, (cls._NO_CATEGORY_CAPTION, cls._DEFAULT_COLOR))
        ratio = (value / grand) if grand > 0 else 0.0
        return {
            "category_id": category_id,
            "caption": caption,
            "color": color,
            "amount_cop": value,
            "ratio": cls._clamp_unit(ratio),
        }

    @classmethod
    def _category_meta_for_card(
        cls,
        service: CreditCardService,
        card_id: str,
    ) -> dict[str, tuple[str, str]]:
        out: dict[str, tuple[str, str]] = {}
        for cat in service.categories_for_card(card_id):
            out[cat.category_id] = (cls._caption_for(cat), cat.color or cls._DEFAULT_COLOR)
        return out

    @classmethod
    def _caption_for(cls, cat: CreditCardCategory) -> str:
        return cat.title or cls._NO_CATEGORY_CAPTION

    @classmethod
    def _clamp_unit(cls, value: float) -> float:
        if value < 0:
            return 0.0
        if value > 1:
            return 1.0
        return value
