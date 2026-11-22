"""Income distribution ledger persisted in Cloudflare D1 (production backend of ``MonthlyDistributionRepository``)."""

from __future__ import annotations

from finanmind.models.income_distribution_line import IncomeDistributionLine
from finanmind.models.income_receipt import IncomeReceipt
from finanmind.storage.d1_client import D1Client
from finanmind.storage.d1_table_sync import D1Table, D1TableSync, Row


class MonthlyDistributionD1Repository:
    """Same contract as ``MonthlyDistributionRepository`` (``load_all`` / ``save_all``).

    ``label_id`` points to ``budget_labels``, owned by the budget repository, which
    deletes labels without touching distribution lines: it is a soft reference, so a
    line whose label no longer exists is stored with NULL (read back as ``""``).
    """

    RECEIPTS = D1Table(
        "income_receipts",
        ("receipt_id",),
        ("receipt_id", "occurred_on", "amount_cop", "memo"),
        order_by="occurred_on, receipt_id",
    )
    LINES = D1Table(
        "income_distribution_lines",
        ("line_id",),
        ("line_id", "receipt_id", "label_id", "occurred_on", "amount_cop", "memo"),
        soft_refs={"label_id": "budget_labels.label_id"},
        order_by="receipt_id, occurred_on, line_id",
    )

    def __init__(self, client: D1Client) -> None:
        self._client = client
        self._receipts = D1TableSync(self.RECEIPTS)
        self._lines = D1TableSync(self.LINES)

    def load_all(self) -> tuple[list[IncomeReceipt], list[IncomeDistributionLine]]:
        """Return receipts and allocation lines in the order the CSV codec writes them."""
        receipt_rows, line_rows = D1TableSync.read(self._client, [self._receipts, self._lines])
        receipts = [
            IncomeReceipt(
                receipt_id=r["receipt_id"],
                occurred_on=r["occurred_on"],
                amount_cop=float(r["amount_cop"]),
                memo=r["memo"],
            )
            for r in receipt_rows
        ]
        lines = [
            IncomeDistributionLine(
                line_id=r["line_id"],
                receipt_id=r["receipt_id"],
                label_id=r["label_id"] or "",
                occurred_on=r["occurred_on"],
                amount_cop=float(r["amount_cop"]),
                memo=r["memo"],
            )
            for r in line_rows
        ]
        return receipts, lines

    def save_all(self, receipts: list[IncomeReceipt], lines: list[IncomeDistributionLine]) -> None:
        """Make both tables equal the given lists in one atomic batch."""
        receipt_rows: list[Row] = [
            {
                "receipt_id": r.receipt_id,
                "occurred_on": r.occurred_on,
                "amount_cop": _cop(r.amount_cop),
                "memo": r.memo,
            }
            for r in receipts
        ]
        line_rows: list[Row] = [
            {
                "line_id": ln.line_id,
                "receipt_id": ln.receipt_id,
                "label_id": ln.label_id or None,
                "occurred_on": ln.occurred_on,
                "amount_cop": _cop(ln.amount_cop),
                "memo": ln.memo,
            }
            for ln in lines
        ]
        D1TableSync.write(self._client, [(self._receipts, receipt_rows), (self._lines, line_rows)])


def _cop(amount: float) -> int:
    """COP amounts are stored as whole pesos, like the CSV codec does."""
    return int(round(amount))
