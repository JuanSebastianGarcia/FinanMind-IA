"""CSV codec for investment categories and holdings."""

from __future__ import annotations

import csv
import io

from finanmind.models.investment_category import InvestmentCategory
from finanmind.models.investment_currency_code import InvestmentCurrencyCode
from finanmind.models.investment_entry import InvestmentEntry


class InvestmentCsvCodec:
    """Typed rows: ``category`` definitions plus ``investment`` lines."""

    HEADER = ["record_type", "id", "category_id", "amount_cop", "date_iso", "text1", "text2"]
    ROW_CATEGORY = "category"
    ROW_INVESTMENT = "investment"

    @classmethod
    def to_csv_text(
        cls,
        categories: list[InvestmentCategory],
        entries: list[InvestmentEntry],
    ) -> str:
        """Serialize categories and holdings into one CSV body."""
        buf = io.StringIO(newline="")
        writer = csv.writer(buf)
        writer.writerow(cls.HEADER)
        cls._write_categories(writer, categories)
        cls._write_entries(writer, entries)
        return buf.getvalue()

    @classmethod
    def _write_categories(cls, writer: csv.writer, categories: list[InvestmentCategory]) -> None:
        for cat in sorted(categories, key=lambda c: (c.name.lower(), c.category_id)):
            writer.writerow(cls._category_row(cat))

    @classmethod
    def _category_row(cls, cat: InvestmentCategory) -> list[str]:
        return [cls.ROW_CATEGORY, cat.category_id, "", "0", "", cat.name, ""]

    @classmethod
    def _write_entries(cls, writer: csv.writer, entries: list[InvestmentEntry]) -> None:
        for row in sorted(entries, key=lambda e: (e.invested_date_iso, e.category_id, e.investment_id)):
            writer.writerow(cls._entry_row(row))

    @classmethod
    def _entry_row(cls, entry: InvestmentEntry) -> list[str]:
        return [
            cls.ROW_INVESTMENT,
            entry.investment_id,
            entry.currency_code,
            cls._amount_cell(entry.amount, entry.currency_code),
            entry.invested_date_iso,
            entry.category_id,
            entry.description,
        ]

    @classmethod
    def _amount_cell(cls, amount: float, currency_code: str) -> str:
        if currency_code.upper() == InvestmentCurrencyCode.USD:
            return f"{amount:.2f}"
        return str(int(round(amount)))

    @classmethod
    def from_csv_text(cls, text: str) -> tuple[list[InvestmentCategory], list[InvestmentEntry]]:
        """Parse CSV body into categories and investment rows."""
        body = cls._read_body(text)
        cats = [cls._category_from_row(r) for r in body if cls._kind(r) == cls.ROW_CATEGORY]
        ents = [cls._entry_from_row(r) for r in body if cls._kind(r) == cls.ROW_INVESTMENT]
        return cats, ents

    @classmethod
    def _read_body(cls, text: str) -> list[list[str]]:
        reader = csv.reader(io.StringIO(text))
        rows = list(reader)
        if rows and rows[0] == cls.HEADER:
            return rows[1:]
        return rows

    @classmethod
    def _kind(cls, row: list[str]) -> str:
        return cls._cell(row, 0)

    @classmethod
    def _category_from_row(cls, row: list[str]) -> InvestmentCategory:
        return InvestmentCategory(category_id=cls._cell(row, 1), name=cls._cell(row, 5))

    @classmethod
    def _entry_from_row(cls, row: list[str]) -> InvestmentEntry:
        ccy = InvestmentCurrencyCode.from_storage_cell(cls._cell(row, 2))
        return InvestmentEntry(
            investment_id=cls._cell(row, 1),
            category_id=cls._cell(row, 5),
            amount=cls._parse_amount(cls._cell(row, 3)),
            currency_code=ccy,
            invested_date_iso=cls._cell(row, 4),
            description=cls._cell(row, 6),
        )

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
