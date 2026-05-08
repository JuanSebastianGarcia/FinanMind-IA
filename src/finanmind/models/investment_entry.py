"""Single registered holding in the user's investment portfolio."""

from dataclasses import dataclass


@dataclass
class InvestmentEntry:
    """Amount in COP or USD linked to one investment category (name = activo)."""

    investment_id: str
    category_id: str
    amount: float
    currency_code: str
    invested_date_iso: str
    description: str
