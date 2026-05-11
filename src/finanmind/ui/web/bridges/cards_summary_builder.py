"""Builds the 4 summary cards shown above the cycle filter in the card detail."""

from __future__ import annotations

from finanmind.models.credit_card import CreditCard
from finanmind.models.credit_card_expense import CreditCardExpense
from finanmind.services.credit_card_balance import CreditCardBalance
from finanmind.services.credit_card_service import CreditCardService


class CardsSummaryBuilder:
    """Assembles ``debt``, ``paid``, ``cycle_spend`` and ``due_day`` for the strip."""

    @classmethod
    def build(
        cls,
        service: CreditCardService,
        card: CreditCard,
        cycle_expenses: list[CreditCardExpense],
    ) -> dict:
        """Compute the four metrics from the service plus the precomputed cycle list."""
        expenses = service.expenses_for_card(card.card_id)
        payments = service.payments_for_card(card.card_id)
        debt = CreditCardBalance.outstanding(expenses, payments)
        paid = CreditCardBalance.total_paid(payments)
        cycle_spend = sum(e.amount_cop for e in cycle_expenses)
        return {
            "debt_cop": debt,
            "paid_cop": paid,
            "cycle_spend_cop": cycle_spend,
            "payment_due_day": card.payment_due_day,
        }
