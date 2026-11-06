"""Serialises cycle expenses into rows with a running total and category caption."""

from __future__ import annotations

from finanmind.models.credit_card_category import CreditCardCategory
from finanmind.models.credit_card_expense import CreditCardExpense
from finanmind.services.credit_card_service import CreditCardService


class CardsExpensesBuilder:
    """Builds the JSON rows for the ``Movimientos del ciclo`` table."""

    _NO_CATEGORY_CAPTION = "Sin categoría"

    @classmethod
    def build(
        cls,
        service: CreditCardService,
        card_id: str,
        cycle_expenses: list[CreditCardExpense],
    ) -> list[dict]:
        """Return one row per expense including a precomputed running total.

        Direct (single-installment) expenses accumulate their own amount, same as
        before. Installment expenses accumulate the *remaining balance* of each
        purchase instead — installments left (including the current one) times the
        installment amount — so the running total reflects outstanding debt rather
        than a historical sum that would keep growing even for cuotas already paid.
        """
        captions = cls._captions_for_card(service, card_id)
        out: list[dict] = []
        running_single = 0.0
        running_installments = 0.0
        for ex in cycle_expenses:
            if ex.installments > 1:
                remaining_installments = ex.installments - ex.installment_number + 1
                running_installments += remaining_installments * ex.amount_cop
                running_value = running_installments
            else:
                running_single += ex.amount_cop
                running_value = running_single
            out.append(cls._row(ex, running_value, captions))
        return out

    @classmethod
    def _row(cls, ex: CreditCardExpense, running_total: float, captions: dict[str, str]) -> dict:
        return {
            "expense_id": ex.expense_id,
            "occurred_on": ex.occurred_on,
            "description": ex.description,
            "category_id": ex.category_id,
            "category_caption": cls._caption(ex.category_id, captions),
            "amount_cop": ex.amount_cop,
            "installments": ex.installments,
            "installment_number": ex.installment_number,
            "total_amount_cop": ex.total_amount_cop,
            "parent_expense_id": ex.parent_expense_id,
            "notes": ex.notes,
            "running_total_cop": running_total,
        }

    @classmethod
    def _captions_for_card(cls, service: CreditCardService, card_id: str) -> dict[str, str]:
        out: dict[str, str] = {}
        for cat in service.categories_for_card(card_id):
            out[cat.category_id] = cat.title or cls._NO_CATEGORY_CAPTION
        return out

    @classmethod
    def _caption(cls, category_id: str, captions: dict[str, str]) -> str:
        if category_id == "":
            return cls._NO_CATEGORY_CAPTION
        return captions.get(category_id, cls._NO_CATEGORY_CAPTION)
