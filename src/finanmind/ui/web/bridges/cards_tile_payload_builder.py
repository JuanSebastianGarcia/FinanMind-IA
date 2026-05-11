"""Serialises each credit card into the tile payload the dashboard renders."""

from __future__ import annotations

from finanmind.models.credit_card import CreditCard
from finanmind.services.credit_card_balance import CreditCardBalance
from finanmind.services.credit_card_service import CreditCardService


class CardsTilePayloadBuilder:
    """Builds one dict per card with debt, available credit, usage ratio and tone."""

    @classmethod
    def build_many(cls, service: CreditCardService) -> list[dict]:
        """Return tile payloads in the same order ``cards_snapshot`` provides them."""
        return [cls._build_one(service, card) for card in service.cards_snapshot()]

    @classmethod
    def _build_one(cls, service: CreditCardService, card: CreditCard) -> dict:
        expenses = service.expenses_for_card(card.card_id)
        payments = service.payments_for_card(card.card_id)
        debt = CreditCardBalance.outstanding(expenses, payments)
        available = CreditCardBalance.available_credit(card.limit_cop, expenses, payments)
        ratio = CreditCardBalance.usage_ratio(card.limit_cop, expenses, payments)
        return cls._compose(card, debt, available, ratio)

    @classmethod
    def _compose(cls, card: CreditCard, debt: float, available: float, ratio: float) -> dict:
        return {
            "card_id": card.card_id,
            "name": card.name,
            "color": card.color,
            "cut_day": card.cut_day,
            "payment_due_day": card.payment_due_day,
            "limit_cop": card.limit_cop,
            "debt_cop": debt,
            "available_cop": available,
            "usage_ratio": ratio,
            "usage_tone": cls._tone(ratio),
        }

    @classmethod
    def _tone(cls, ratio: float) -> str:
        if ratio >= 0.85:
            return "over"
        if ratio >= 0.6:
            return "warn"
        return "ok"
