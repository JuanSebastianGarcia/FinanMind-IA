"""Builds the ledger rows shown in the Distribución left panel."""

from __future__ import annotations

from finanmind.models.budget_workspace import BudgetWorkspace
from finanmind.models.income_distribution_line import IncomeDistributionLine
from finanmind.models.income_receipt import IncomeReceipt
from finanmind.services.monthly_distribution_service import MonthlyDistributionService


class DistributionLedgerBuilder:
    """Produces an income row plus allocation rows with running balance."""

    @classmethod
    def build(
        cls,
        ledger: MonthlyDistributionService,
        workspace: BudgetWorkspace,
        receipt_id: str | None,
    ) -> list[dict]:
        """Return the rows array; empty when no receipt is selected."""
        if not receipt_id:
            return []
        receipt = ledger.receipt_by_id(receipt_id)
        lines = ledger.lines_for_receipt(receipt_id)
        out: list[dict] = [cls._income_row(receipt)]
        cls._append_line_rows(out, lines, workspace, receipt.amount_cop)
        return out

    @classmethod
    def _income_row(cls, receipt: IncomeReceipt) -> dict:
        return {
            "kind": "income",
            "id": receipt.receipt_id,
            "occurred_on": receipt.occurred_on,
            "memo": receipt.memo,
            "amount_cop": receipt.amount_cop,
            "balance_cop": receipt.amount_cop,
        }

    @classmethod
    def _append_line_rows(
        cls,
        out: list[dict],
        lines: list[IncomeDistributionLine],
        workspace: BudgetWorkspace,
        opening_balance: float,
    ) -> None:
        balance = opening_balance
        for ln in lines:
            balance -= ln.amount_cop
            out.append(cls._line_row(ln, workspace, balance))

    @classmethod
    def _line_row(cls, ln: IncomeDistributionLine, workspace: BudgetWorkspace, balance: float) -> dict:
        return {
            "kind": "line",
            "id": ln.line_id,
            "label_id": ln.label_id,
            "label_title": cls._label_title(workspace, ln.label_id),
            "occurred_on": ln.occurred_on,
            "memo": ln.memo,
            "amount_cop": ln.amount_cop,
            "balance_cop": balance,
        }

    @classmethod
    def _label_title(cls, workspace: BudgetWorkspace, label_id: str) -> str:
        for cat in workspace.categories:
            for lbl in cat.labels:
                if lbl.label_id == label_id:
                    return lbl.title or "Etiqueta"
        return "Etiqueta"
