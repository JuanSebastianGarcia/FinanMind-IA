"""Builds the credit-card link choices shown inside the label dialog."""

from __future__ import annotations

from finanmind.services.credit_card_service import CreditCardService


class CcLinkOptionsBuilder:
    """Produces JSON-friendly ``card → category`` options for the link dropdown."""

    @classmethod
    def build(cls, cards: CreditCardService | None) -> list[dict]:
        """Return one entry per credit-card category, captioned ``Card → Category``."""
        if cards is None:
            return []
        out: list[dict] = []
        for card in cards.cards_snapshot():
            cls._append_card_options(out, cards, card.card_id, card.name)
        return out

    @classmethod
    def _append_card_options(
        cls,
        out: list[dict],
        cards: CreditCardService,
        card_id: str,
        card_name: str,
    ) -> None:
        for cat in cards.categories_for_card(card_id):
            out.append({
                "label": f"{card_name} → {cat.title}",
                "cc_category_id": cat.category_id,
            })
