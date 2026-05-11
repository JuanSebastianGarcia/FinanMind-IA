"""Serialises a card's registered payments sorted newest-first."""

from __future__ import annotations

from finanmind.models.credit_card_payment import CreditCardPayment
from finanmind.services.credit_card_service import CreditCardService


class CardsPaymentsBuilder:
    """Returns the payments list ordered by date descending for the right panel."""

    @classmethod
    def build(cls, service: CreditCardService, card_id: str) -> list[dict]:
        """Return payments sorted by date descending so newest entries appear first."""
        payments = sorted(
            service.payments_for_card(card_id),
            key=lambda p: p.paid_on,
            reverse=True,
        )
        return [cls._row(p) for p in payments]

    @classmethod
    def _row(cls, pay: CreditCardPayment) -> dict:
        return {
            "payment_id": pay.payment_id,
            "paid_on": pay.paid_on,
            "amount_cop": pay.amount_cop,
            "notes": pay.notes,
        }
