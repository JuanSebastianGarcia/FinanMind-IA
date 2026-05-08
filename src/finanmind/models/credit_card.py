"""Credit card entity persisted in the workspace."""

from dataclasses import dataclass


@dataclass
class CreditCard:
    """Card alias, total limit, billing cycle days, and visual identifier."""

    card_id: str
    name: str
    limit_cop: float
    cut_day: int
    payment_due_day: int
    color: str
