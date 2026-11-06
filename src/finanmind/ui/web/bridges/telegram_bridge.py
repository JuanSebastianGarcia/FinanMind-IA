"""Adapter from the JavaScript layer to the background Telegram purchase reader."""

from __future__ import annotations

from finanmind.services.credit_card_service import CreditCardService
from finanmind.services.telegram_card_termination_store import TelegramCardTerminationStore
from finanmind.services.telegram_expense_sync import TelegramExpenseSync
from finanmind.services.telegram_sync_state_store import TelegramSyncStateStore
from finanmind.ui.web.bridges.telegram_pending_rows_builder import TelegramPendingRowsBuilder


class TelegramBridge:
    """Exposes the queued Telegram purchases and the actions to route/settle them."""

    def __init__(self, cards: CreditCardService, sync: TelegramExpenseSync) -> None:
        self._cards = cards
        self._sync = sync

    def status(self) -> dict:
        """Return reader state, last read time, queued purchases and the card choices."""
        snapshot = self._sync.status()
        return {
            "state": snapshot["state"],
            "error": snapshot["error"],
            "last_read_at": snapshot["last_read_at"],
            "purchases": TelegramPendingRowsBuilder.build_many(self._cards, snapshot["pending"]),
            "cards": [{"card_id": card.card_id, "name": card.name} for card in self._cards.cards_snapshot()],
        }

    def assign_termination(self, last4: str, card_id: str) -> None:
        """Remember which card purchases ending in ``last4`` belong to."""
        TelegramCardTerminationStore.assign(last4, card_id)

    def resolve_purchase(self, purchase_id: str) -> None:
        """Drop a purchase from the queue once registered or skipped as duplicate."""
        TelegramSyncStateStore.resolve(purchase_id)

    def sync_now(self) -> None:
        """Ask the background reader to check the chat immediately."""
        self._sync.request_sync()
