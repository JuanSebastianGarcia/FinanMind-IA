"""Composes the full Distribución panel snapshot returned to the front-end."""

from __future__ import annotations

from finanmind.budget.book_service import BudgetBookService
from finanmind.services.monthly_distribution_service import MonthlyDistributionService
from finanmind.ui.web.bridges.distribution_ledger_builder import DistributionLedgerBuilder
from finanmind.ui.web.bridges.distribution_months_resolver import DistributionMonthsResolver
from finanmind.ui.web.bridges.distribution_receipts_lister import DistributionReceiptsLister
from finanmind.ui.web.bridges.distribution_summary_builder import DistributionSummaryBuilder


class DistributionStateBuilder:
    """Combines month resolution, receipts, ledger and month summary into one dict."""

    @classmethod
    def build(
        cls,
        book: BudgetBookService,
        ledger: MonthlyDistributionService,
        preferred_month: str,
        preferred_receipt_id: str | None,
    ) -> dict:
        """Return the full state needed to render the Distribución panel."""
        months = DistributionMonthsResolver.list_months(ledger)
        active_month = DistributionMonthsResolver.coerce_active(months, preferred_month)
        receipts = DistributionReceiptsLister.build(ledger, active_month)
        active_receipt = DistributionReceiptsLister.coerce_active(receipts, preferred_receipt_id)
        return cls._assemble(book, ledger, months, active_month, receipts, active_receipt)

    @classmethod
    def _assemble(
        cls,
        book: BudgetBookService,
        ledger: MonthlyDistributionService,
        months: list[str],
        active_month: str,
        receipts: list[dict],
        active_receipt: str | None,
    ) -> dict:
        workspace = book.peek()
        ledger_rows = DistributionLedgerBuilder.build(ledger, workspace, active_receipt)
        summary_rows = DistributionSummaryBuilder.build(workspace, ledger, active_month)
        return {
            "months": months,
            "current_month": DistributionMonthsResolver.current_month_key(),
            "active_month": active_month,
            "receipts": receipts,
            "active_receipt_id": active_receipt,
            "remainder_cop": cls._remainder(ledger, active_receipt),
            "ledger_rows": ledger_rows,
            "summary_rows": summary_rows,
        }

    @classmethod
    def _remainder(cls, ledger: MonthlyDistributionService, receipt_id: str | None) -> float | None:
        if receipt_id is None:
            return None
        return ledger.remaining_for_receipt(receipt_id)
