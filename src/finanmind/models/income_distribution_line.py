"""One allocation from a receipt toward a budget label."""

from dataclasses import dataclass


@dataclass
class IncomeDistributionLine:
    """Spend row tied to a receipt and a budget label identifier."""

    line_id: str
    receipt_id: str
    label_id: str
    occurred_on: str
    amount_cop: float
    memo: str
