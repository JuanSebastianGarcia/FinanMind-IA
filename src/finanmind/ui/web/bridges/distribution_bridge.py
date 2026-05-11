"""High-level adapter from the JavaScript layer to MonthlyDistributionService."""

from __future__ import annotations

from finanmind.budget.book_service import BudgetBookService
from finanmind.services.monthly_distribution_service import MonthlyDistributionService
from finanmind.ui.web.bridges.distribution_label_options_builder import DistributionLabelOptionsBuilder
from finanmind.ui.web.bridges.distribution_state_builder import DistributionStateBuilder


class DistributionBridge:
    """Translates JS commands into ``MonthlyDistributionService`` calls."""

    def __init__(self, book: BudgetBookService, ledger: MonthlyDistributionService) -> None:
        self._book = book
        self._ledger = ledger

    def get_state(self, preferred_month: str, preferred_receipt_id: str | None) -> dict:
        """Snapshot the Distribución panel state honoring the JS selection hints."""
        return DistributionStateBuilder.build(
            self._book,
            self._ledger,
            preferred_month or "",
            preferred_receipt_id,
        )

    def label_options(self) -> list[dict]:
        """Flat list of ``Category · Label`` choices for the line dialog."""
        return DistributionLabelOptionsBuilder.build(self._book.peek())

    def add_receipt(self, occurred_on: str, amount: float, memo: str) -> dict:
        """Persist a new receipt and return its id plus its month for navigation."""
        receipt = self._ledger.add_receipt(occurred_on, float(amount), memo or "")
        return {
            "receipt_id": receipt.receipt_id,
            "month": receipt.occurred_on[:7],
        }

    def delete_receipt(self, receipt_id: str) -> None:
        """Remove a receipt and all its allocations."""
        self._ledger.delete_receipt(receipt_id)

    def add_line(
        self,
        receipt_id: str,
        label_id: str,
        occurred_on: str,
        amount: float,
        memo: str,
    ) -> None:
        """Append a new allocation under one receipt."""
        workspace = self._book.peek()
        self._ledger.add_line(receipt_id, label_id, occurred_on, float(amount), memo or "", workspace)

    def delete_line(self, line_id: str) -> None:
        """Remove one allocation row."""
        self._ledger.delete_line(line_id)
