"""High-level adapter from the JavaScript layer to the Budget services."""

from __future__ import annotations

from finanmind.budget.book_service import BudgetBookService
from finanmind.budget.palette import BudgetCategoryPalette
from finanmind.services.credit_card_service import CreditCardService
from finanmind.ui.web.bridges.budget_payload_builder import BudgetPayloadBuilder
from finanmind.ui.web.bridges.cc_link_options_builder import CcLinkOptionsBuilder


class BudgetBridge:
    """Translates JS commands into ``BudgetBookService`` and ``CreditCardService`` calls."""

    def __init__(self, book: BudgetBookService, cards: CreditCardService | None = None) -> None:
        self._book = book
        self._cards = cards

    def get_state(self) -> dict:
        """Snapshot the entire budget workspace as a JSON-friendly dict."""
        return BudgetPayloadBuilder.build(self._book.peek(), self._cards)

    def set_salary(self, amount: float) -> dict:
        """Persist a new salary baseline and return the refreshed state."""
        self._book.set_salary_cop(float(amount))
        return self.get_state()

    def add_category(self, title: str, color: str) -> dict:
        """Append a category and return the refreshed state."""
        self._book.add_category(title, color)
        return self.get_state()

    def update_category(self, category_id: str, title: str, color: str) -> dict:
        """Edit one category and return the refreshed state."""
        self._book.update_category(category_id, title, color)
        return self.get_state()

    def delete_category(self, category_id: str) -> dict:
        """Drop one category (and its labels) and return the refreshed state."""
        self._book.delete_category(category_id)
        return self.get_state()

    def add_label(self, category_id: str, title: str, amount: float, link_id: str) -> dict:
        """Append a label and optionally bind it to a credit-card category."""
        new_label = self._book.add_label(category_id, title, float(amount))
        self._apply_link(new_label.label_id, link_id)
        return self.get_state()

    def update_label(
        self,
        category_id: str,
        label_id: str,
        title: str,
        amount: float,
        link_id: str,
    ) -> dict:
        """Edit one label and re-apply its credit-card link."""
        self._book.update_label(category_id, label_id, title, float(amount))
        self._apply_link(label_id, link_id)
        return self.get_state()

    def delete_label(self, category_id: str, label_id: str) -> dict:
        """Remove a single label and return the refreshed state."""
        self._book.delete_label(category_id, label_id)
        return self.get_state()

    def next_palette_color(self) -> str:
        """Suggest the next preset tone when opening the add-category dialog."""
        return self._book.next_palette()

    def palette_presets(self) -> list[str]:
        """Return every tile colour available in the category dialog palette."""
        return list(BudgetCategoryPalette.PRESETS)

    def cc_link_options(self) -> list[dict]:
        """Return the credit-card link choices presented in the label dialog."""
        return CcLinkOptionsBuilder.build(self._cards)

    def _apply_link(self, label_id: str, link_id: str) -> None:
        if self._cards is None:
            return
        try:
            self._cards.set_link_for_label(label_id, link_id or "")
        except KeyError:
            return
