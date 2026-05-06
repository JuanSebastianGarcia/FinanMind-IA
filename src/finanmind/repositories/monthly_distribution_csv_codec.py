"""CSV codec for income receipts and distribution lines."""

from __future__ import annotations

import csv
import io

from finanmind.models.income_distribution_line import IncomeDistributionLine
from finanmind.models.income_receipt import IncomeReceipt


class MonthlyDistributionCsvCodec:
    """Single-table CSV mixing receipt rows and allocation rows."""

    HEADER = ["record_type", "id", "receipt_id", "occurred_on", "label_id", "amount_cop", "memo"]
    ROW_INCOME = "income"
    ROW_ALLOCATION = "allocation"

    @classmethod
    def to_csv_text(
        cls,
        receipts: list[IncomeReceipt],
        lines: list[IncomeDistributionLine],
    ) -> str:
        """Serialize receipts then allocation lines."""
        buffer = io.StringIO(newline="")
        writer = csv.writer(buffer)
        writer.writerow(cls.HEADER)
        cls._write_receipts(writer, receipts)
        cls._write_lines(writer, lines)
        return buffer.getvalue()

    @classmethod
    def _write_receipts(cls, writer: csv.writer, receipts: list[IncomeReceipt]) -> None:
        ordered = sorted(receipts, key=lambda r: (r.occurred_on, r.receipt_id))
        for rec in ordered:
            writer.writerow(
                [
                    cls.ROW_INCOME,
                    rec.receipt_id,
                    "",
                    rec.occurred_on,
                    "",
                    cls._amount_cell(rec.amount_cop),
                    rec.memo,
                ],
            )

    @classmethod
    def _write_lines(cls, writer: csv.writer, lines: list[IncomeDistributionLine]) -> None:
        ordered = sorted(lines, key=lambda ln: (ln.receipt_id, ln.occurred_on, ln.line_id))
        for ln in ordered:
            writer.writerow(
                [
                    cls.ROW_ALLOCATION,
                    ln.line_id,
                    ln.receipt_id,
                    ln.occurred_on,
                    ln.label_id,
                    cls._amount_cell(ln.amount_cop),
                    ln.memo,
                ],
            )

    @classmethod
    def _amount_cell(cls, amount: float) -> str:
        return str(int(round(amount)))

    @classmethod
    def from_csv_text(cls, text: str) -> tuple[list[IncomeReceipt], list[IncomeDistributionLine]]:
        """Parse CSV into receipts and lines."""
        reader = csv.reader(io.StringIO(text))
        rows = list(reader)
        if not rows:
            return [], []
        body = cls._strip_header(rows)
        receipts = cls._parse_receipts(body)
        lines = cls._parse_lines(body)
        return receipts, lines

    @classmethod
    def _strip_header(cls, rows: list[list[str]]) -> list[list[str]]:
        if rows and rows[0] == cls.HEADER:
            return rows[1:]
        return rows

    @classmethod
    def _parse_receipts(cls, body: list[list[str]]) -> list[IncomeReceipt]:
        out = []
        for row in body:
            if cls._kind(row) != cls.ROW_INCOME:
                continue
            out.append(cls._receipt_from_row(row))
        return out

    @classmethod
    def _parse_lines(cls, body: list[list[str]]) -> list[IncomeDistributionLine]:
        out = []
        for row in body:
            if cls._kind(row) != cls.ROW_ALLOCATION:
                continue
            out.append(cls._line_from_row(row))
        return out

    @classmethod
    def _receipt_from_row(cls, row: list[str]) -> IncomeReceipt:
        rid = cls._cell(row, 1)
        day = cls._cell(row, 3)
        amt = cls._parse_amount(cls._cell(row, 5))
        memo = cls._cell(row, 6)
        return IncomeReceipt(receipt_id=rid, occurred_on=day, amount_cop=amt, memo=memo)

    @classmethod
    def _line_from_row(cls, row: list[str]) -> IncomeDistributionLine:
        lid = cls._cell(row, 1)
        rid = cls._cell(row, 2)
        day = cls._cell(row, 3)
        lab = cls._cell(row, 4)
        amt = cls._parse_amount(cls._cell(row, 5))
        memo = cls._cell(row, 6)
        return IncomeDistributionLine(
            line_id=lid,
            receipt_id=rid,
            label_id=lab,
            occurred_on=day,
            amount_cop=amt,
            memo=memo,
        )

    @classmethod
    def _kind(cls, row: list[str]) -> str:
        return cls._cell(row, 0)

    @classmethod
    def _cell(cls, row: list[str], idx: int) -> str:
        if idx >= len(row):
            return ""
        return row[idx].strip()

    @classmethod
    def _parse_amount(cls, raw: str) -> float:
        if raw == "":
            return 0.0
        try:
            return float(raw)
        except ValueError:
            return 0.0
