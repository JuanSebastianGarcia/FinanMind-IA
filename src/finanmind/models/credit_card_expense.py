"""Single purchase or charge made with a credit card."""

from dataclasses import dataclass


@dataclass
class CreditCardExpense:
    """Charge amount stored with a free-form date independent of the system clock."""

    expense_id: str
    card_id: str
    category_id: str
    occurred_on: str
    amount_cop: float
    description: str
    installments: int
    notes: str
