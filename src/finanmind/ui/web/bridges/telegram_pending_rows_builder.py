"""Serializes queued Telegram purchases into rows the expense-registration flow understands."""

from __future__ import annotations

from finanmind.services.credit_card_service import CreditCardService
from finanmind.services.telegram_card_termination_store import TelegramCardTerminationStore


class TelegramPendingRowsBuilder:
    """Shapes each purchase like a statement row (``occurred_on``/``description``/
    ``value``/``installments``) so ``CardsBridge.classify_extracted_expense`` and
    ``register_extracted_expense`` handle it unchanged, plus the card it routes to."""

    @classmethod
    def build_many(cls, cards: CreditCardService, purchases: list[dict]) -> list[dict]:
        existing_ids = {card.card_id for card in cards.cards_snapshot()}
        return [cls._build(purchase, existing_ids) for purchase in purchases]

    @classmethod
    def _build(cls, purchase: dict, existing_ids: set[str]) -> dict:
        card_id = TelegramCardTerminationStore.lookup(purchase["last4"]) or ""
        return {
            "purchase_id": purchase["purchase_id"],
            "occurred_on": purchase["occurred_on"],
            "description": purchase["merchant"],
            "value": purchase["value"],
            # Notifications never say how many installments a purchase was split
            # into, so it is booked as a single charge.
            "installments": "1 de 1",
            "last4": purchase["last4"],
            "card_id": card_id if card_id in existing_ids else "",
        }
