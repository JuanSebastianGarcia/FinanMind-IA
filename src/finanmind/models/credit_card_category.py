"""Spending category attached to a single credit card."""

from dataclasses import dataclass


@dataclass
class CreditCardCategory:
    """Per-card grouping label used to classify expenses."""

    category_id: str
    card_id: str
    title: str
    color: str
