"""Spending category attached to a single credit card."""

from dataclasses import dataclass


@dataclass
class CreditCardCategory:
    """Per-card grouping label used to classify expenses; may link to a budget label."""

    category_id: str
    card_id: str
    title: str
    color: str
    linked_label_id: str = ""
