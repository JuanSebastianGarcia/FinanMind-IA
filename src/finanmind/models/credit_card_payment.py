"""Payment registered against a credit card balance."""

from dataclasses import dataclass


@dataclass
class CreditCardPayment:
    """Money applied to a card, reducing the running debt."""

    payment_id: str
    card_id: str
    paid_on: str
    amount_cop: float
    notes: str
