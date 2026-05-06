"""Budget line item under a category."""

from dataclasses import dataclass


@dataclass
class BudgetLabel:
    """Named budget bucket with an amount in COP."""

    label_id: str
    title: str
    amount_cop: float
