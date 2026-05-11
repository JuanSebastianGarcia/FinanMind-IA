"""Serialises the receipts of a month for the Distribución receipt dropdown."""

from __future__ import annotations

from finanmind.models.income_receipt import IncomeReceipt
from finanmind.services.monthly_distribution_service import MonthlyDistributionService


class DistributionReceiptsLister:
    """Returns the JSON-ready list of receipts visible in the active month."""

    @classmethod
    def build(cls, ledger: MonthlyDistributionService, month_key: str) -> list[dict]:
        """Return receipts ordered as the service exposes them (newest first)."""
        return [cls._receipt_payload(r) for r in ledger.receipts_in_month(month_key)]

    @classmethod
    def coerce_active(cls, receipts: list[dict], preferred: str | None) -> str | None:
        """Pick the preferred receipt id when valid, otherwise the first available."""
        if not receipts:
            return None
        ids = {r["receipt_id"] for r in receipts}
        token = (preferred or "").strip()
        if token in ids:
            return token
        return receipts[0]["receipt_id"]

    @classmethod
    def _receipt_payload(cls, receipt: IncomeReceipt) -> dict:
        return {
            "receipt_id": receipt.receipt_id,
            "occurred_on": receipt.occurred_on,
            "amount_cop": receipt.amount_cop,
            "memo": receipt.memo,
        }
