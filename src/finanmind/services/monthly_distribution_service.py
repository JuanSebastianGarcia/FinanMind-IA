"""Income receipts and per-tag allocations backed by CSV persistence."""

from __future__ import annotations

import uuid

from finanmind.models.budget_workspace import BudgetWorkspace
from finanmind.models.income_distribution_line import IncomeDistributionLine
from finanmind.models.income_receipt import IncomeReceipt
from finanmind.repositories.monthly_distribution_repository import MonthlyDistributionRepository


class MonthlyDistributionService:
    """CRUD plus aggregates for payroll receipts and budget-tag splits."""

    def __init__(self, repository: MonthlyDistributionRepository) -> None:
        self._repository = repository
        self._receipts: list[IncomeReceipt] = []
        self._lines: list[IncomeDistributionLine] = []

    def load(self) -> None:
        """Reload receipts and lines from disk."""
        self._receipts, self._lines = self._repository.load_all()

    def persist(self) -> None:
        """Flush in-memory ledger."""
        self._repository.save_all(self._receipts, self._lines)

    def receipts_snapshot(self) -> tuple[list[IncomeReceipt], list[IncomeDistributionLine]]:
        """Return shallow copies for read-only consumers."""
        return list(self._receipts), list(self._lines)

    def add_receipt(self, occurred_on: str, amount_cop: float, memo: str) -> IncomeReceipt:
        """Append a new receipt row."""
        self._assert_positive(amount_cop)
        day = self._require_iso_day(occurred_on)
        rid = str(uuid.uuid4())
        rec = IncomeReceipt(receipt_id=rid, occurred_on=day, amount_cop=amount_cop, memo=memo.strip())
        self._receipts.append(rec)
        self.persist()
        return rec

    def delete_receipt(self, receipt_id: str) -> None:
        """Remove receipt plus dependent allocations."""
        before = len(self._receipts)
        self._receipts = [r for r in self._receipts if r.receipt_id != receipt_id]
        if len(self._receipts) == before:
            raise KeyError("Ingreso no encontrado")
        self._lines = [ln for ln in self._lines if ln.receipt_id != receipt_id]
        self.persist()

    def add_line(
        self,
        receipt_id: str,
        label_id: str,
        occurred_on: str,
        amount_cop: float,
        memo: str,
        workspace: BudgetWorkspace,
    ) -> IncomeDistributionLine:
        """Append an allocation tied to a receipt and budget label."""
        self._require_receipt(receipt_id)
        self._assert_label_registered(workspace, label_id)
        self._assert_positive(amount_cop)
        day = self._require_iso_day(occurred_on)
        lid = str(uuid.uuid4())
        row = IncomeDistributionLine(
            line_id=lid,
            receipt_id=receipt_id,
            label_id=label_id.strip(),
            occurred_on=day,
            amount_cop=amount_cop,
            memo=memo.strip(),
        )
        self._lines.append(row)
        self.persist()
        return row

    def delete_line(self, line_id: str) -> None:
        """Remove one allocation."""
        before = len(self._lines)
        self._lines = [ln for ln in self._lines if ln.line_id != line_id]
        if len(self._lines) == before:
            raise KeyError("Movimiento no encontrado")
        self.persist()

    def receipt_by_id(self, receipt_id: str) -> IncomeReceipt:
        """Lookup receipt by identifier."""
        for rec in self._receipts:
            if rec.receipt_id == receipt_id:
                return rec
        raise KeyError("Ingreso no encontrado")

    def lines_for_receipt(self, receipt_id: str) -> list[IncomeDistributionLine]:
        """Return allocations sorted by date."""
        bucket = [ln for ln in self._lines if ln.receipt_id == receipt_id]
        return sorted(bucket, key=lambda ln: (ln.occurred_on, ln.line_id))

    def allocated_total(self, receipt_id: str) -> float:
        """Sum allocations for one receipt."""
        return sum(ln.amount_cop for ln in self.lines_for_receipt(receipt_id))

    def remaining_for_receipt(self, receipt_id: str) -> float:
        """Receipt amount minus allocations."""
        rec = self.receipt_by_id(receipt_id)
        return rec.amount_cop - self.allocated_total(receipt_id)

    def receipts_in_month(self, month_prefix: str) -> list[IncomeReceipt]:
        """Receipts whose pay date falls inside ``yyyy-mm``."""
        prefix = month_prefix.strip()
        hits = [r for r in self._receipts if r.occurred_on.startswith(prefix)]
        return sorted(hits, key=lambda r: (r.occurred_on, r.receipt_id), reverse=True)

    def monthly_spent_by_label(self, month_prefix: str) -> dict[str, float]:
        """Totals allocated in the month by label identifier."""
        prefix = month_prefix.strip()
        totals: dict[str, float] = {}
        for ln in self._lines:
            if not ln.occurred_on.startswith(prefix):
                continue
            totals[ln.label_id] = totals.get(ln.label_id, 0.0) + ln.amount_cop
        return totals

    def known_month_prefixes(self) -> list[str]:
        """Distinct ``yyyy-mm`` values present in receipts or lines."""
        tokens: set[str] = set()
        for rec in self._receipts:
            mp = self._month_prefix(rec.occurred_on)
            if mp:
                tokens.add(mp)
        for ln in self._lines:
            mp = self._month_prefix(ln.occurred_on)
            if mp:
                tokens.add(mp)
        ordered = sorted(tokens, reverse=True)
        return ordered

    def _require_receipt(self, receipt_id: str) -> IncomeReceipt:
        return self.receipt_by_id(receipt_id)

    def _assert_label_registered(self, workspace: BudgetWorkspace, label_id: str) -> None:
        token = label_id.strip()
        if token == "":
            raise ValueError("Selecciona una etiqueta")
        for cat in workspace.categories:
            for lbl in cat.labels:
                if lbl.label_id == token:
                    return
        raise ValueError("La etiqueta no existe en el presupuesto")

    def _assert_positive(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("El monto debe ser mayor que cero")

    def _require_iso_day(self, raw: str) -> str:
        day = raw.strip()
        if len(day) != 10 or day[4] != "-" or day[7] != "-":
            raise ValueError("Usa la fecha en formato AAAA-MM-DD")
        return day

    def _month_prefix(self, iso_day: str) -> str:
        if len(iso_day) >= 7:
            return iso_day[:7]
        return ""
