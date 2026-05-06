"""Single payroll or income deposit available for distribution."""

from dataclasses import dataclass


@dataclass
class IncomeReceipt:
    """Money received on a date (e.g. bi-weekly payroll) to allocate across tags."""

    receipt_id: str
    occurred_on: str
    amount_cop: float
    memo: str
