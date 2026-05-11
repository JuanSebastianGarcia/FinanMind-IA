"""High-level adapter from the JavaScript layer to the credit-card services."""

from __future__ import annotations

from finanmind.budget.book_service import BudgetBookService
from finanmind.budget.palette import BudgetCategoryPalette
from finanmind.services.credit_card_service import CreditCardService
from finanmind.ui.web.bridges.cards_detail_state_builder import CardsDetailStateBuilder
from finanmind.ui.web.bridges.cards_label_options_builder import CardsLabelOptionsBuilder
from finanmind.ui.web.bridges.cards_tile_payload_builder import CardsTilePayloadBuilder


class CardsBridge:
    """Translates JS commands into ``CreditCardService`` calls."""

    def __init__(self, book: BudgetBookService, cards: CreditCardService) -> None:
        self._book = book
        self._cards = cards

    def dashboard_state(self) -> dict:
        """Return the snapshot used by the cards dashboard grid."""
        return {"cards": CardsTilePayloadBuilder.build_many(self._cards)}

    def detail_state(self, card_id: str, preferred_cycle: str) -> dict:
        """Return the snapshot used by the single-card detail view."""
        return CardsDetailStateBuilder.build(self._cards, self._book, card_id, preferred_cycle or "")

    def label_options(self) -> list[dict]:
        """Return the budget-label options used by the card-category dialog."""
        return CardsLabelOptionsBuilder.build(self._book)

    def palette_presets(self) -> list[str]:
        """Return the colour presets shared with the budget palette."""
        return list(BudgetCategoryPalette.PRESETS)

    def add_card(
        self,
        name: str,
        limit: float,
        cut_day: int,
        payment_due_day: int,
        color: str,
    ) -> dict:
        """Persist a new card and return its identifier for navigation."""
        card = self._cards.add_card(name, float(limit), int(cut_day), int(payment_due_day), color or "")
        return {"card_id": card.card_id}

    def update_card(
        self,
        card_id: str,
        name: str,
        limit: float,
        cut_day: int,
        payment_due_day: int,
        color: str,
    ) -> None:
        """Mutate an existing card in place."""
        self._cards.update_card(card_id, name, float(limit), int(cut_day), int(payment_due_day), color or "")

    def delete_card(self, card_id: str) -> None:
        """Remove a card plus all its categories, expenses and payments."""
        self._cards.delete_card(card_id)

    def add_category(self, card_id: str, title: str, color: str, link_id: str) -> None:
        """Insert a new category bound to a card and (optional) budget label."""
        self._cards.add_category(card_id, title, color or "", link_id or "")

    def update_category(self, category_id: str, title: str, color: str, link_id: str) -> None:
        """Edit one card category and (re)apply its budget-label link."""
        self._cards.update_category(category_id, title, color or "", link_id or "")

    def delete_category(self, category_id: str) -> None:
        """Remove one category and clear it from existing expenses."""
        self._cards.delete_category(category_id)

    def add_expense(
        self,
        card_id: str,
        category_id: str,
        occurred_on: str,
        amount: float,
        description: str,
        installments: int,
        notes: str,
    ) -> None:
        """Append a new charge for one card."""
        self._cards.add_expense(
            card_id, category_id or "", occurred_on, float(amount), description, int(installments), notes or "",
        )

    def update_expense(
        self,
        expense_id: str,
        category_id: str,
        occurred_on: str,
        amount: float,
        description: str,
        installments: int,
        notes: str,
    ) -> None:
        """Mutate an existing charge in place."""
        self._cards.update_expense(
            expense_id, category_id or "", occurred_on, float(amount), description, int(installments), notes or "",
        )

    def delete_expense(self, expense_id: str) -> None:
        """Remove one charge from the card history."""
        self._cards.delete_expense(expense_id)

    def add_payment(self, card_id: str, paid_on: str, amount: float, notes: str) -> None:
        """Register a payment reducing the card debt."""
        self._cards.add_payment(card_id, paid_on, float(amount), notes or "")

    def delete_payment(self, payment_id: str) -> None:
        """Remove one payment from the card history."""
        self._cards.delete_payment(payment_id)
