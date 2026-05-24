"""CSV codec for credit cards plus their categories, expenses, and payments."""

from __future__ import annotations

import csv
import io

from finanmind.models.credit_card import CreditCard
from finanmind.models.credit_card_category import CreditCardCategory
from finanmind.models.credit_card_expense import CreditCardExpense
from finanmind.models.credit_card_payment import CreditCardPayment


class CreditCardCsvCodec:
    """Single-table CSV mixing card, category, expense, and payment rows."""

    HEADER = [
        "record_type",
        "row_id",
        "card_id",
        "ref_id",
        "day",
        "amount_cop",
        "text1",
        "text2",
        "color",
        "day_a",
        "day_b",
        "installments",
        "total_amount_cop",
        "installment_number",
        "parent_expense_id",
        "entry_order",
    ]
    ROW_CARD = "card"
    ROW_CATEGORY = "category"
    ROW_EXPENSE = "expense"
    ROW_PAYMENT = "payment"

    @classmethod
    def to_csv_text(
        cls,
        cards: list[CreditCard],
        categories: list[CreditCardCategory],
        expenses: list[CreditCardExpense],
        payments: list[CreditCardPayment],
    ) -> str:
        """Serialize all entity types into one CSV body."""
        buf = io.StringIO(newline="")
        writer = csv.writer(buf)
        writer.writerow(cls.HEADER)
        cls._write_cards(writer, cards)
        cls._write_categories(writer, categories)
        cls._write_expenses(writer, expenses)
        cls._write_payments(writer, payments)
        return buf.getvalue()

    @classmethod
    def _write_cards(cls, writer: csv.writer, cards: list[CreditCard]) -> None:
        for card in sorted(cards, key=lambda c: (c.name, c.card_id)):
            writer.writerow(cls._card_row(card))

    @classmethod
    def _card_row(cls, card: CreditCard) -> list[str]:
        return [
            cls.ROW_CARD,
            card.card_id,
            "",
            "",
            "",
            cls._amount_cell(card.limit_cop),
            card.name,
            "",
            card.color,
            str(int(card.cut_day)),
            str(int(card.payment_due_day)),
            "",
            "",
            "",
            "",
            "",
        ]

    @classmethod
    def _write_categories(cls, writer: csv.writer, cats: list[CreditCardCategory]) -> None:
        for cat in sorted(cats, key=lambda c: (c.card_id, c.title, c.category_id)):
            writer.writerow(cls._category_row(cat))

    @classmethod
    def _category_row(cls, cat: CreditCardCategory) -> list[str]:
        return [
            cls.ROW_CATEGORY,
            cat.category_id,
            cat.card_id,
            "",
            "",
            "",
            cat.title,
            cat.linked_label_id,
            cat.color,
            "",
            "",
            "",
            "",
            "",
            "",
            "",
        ]

    @classmethod
    def _write_expenses(cls, writer: csv.writer, exps: list[CreditCardExpense]) -> None:
        for ex in sorted(exps, key=lambda e: (e.card_id, e.occurred_on, e.expense_id)):
            writer.writerow(cls._expense_row(ex))

    @classmethod
    def _expense_row(cls, ex: CreditCardExpense) -> list[str]:
        return [
            cls.ROW_EXPENSE,
            ex.expense_id,
            ex.card_id,
            ex.category_id,
            ex.occurred_on,
            cls._amount_cell(ex.amount_cop),
            ex.description,
            ex.notes,
            "",
            "",
            "",
            str(int(ex.installments)),
            cls._amount_cell(ex.total_amount_cop),
            str(int(ex.installment_number)),
            ex.parent_expense_id,
            str(int(ex.entry_order)),
        ]

    @classmethod
    def _write_payments(cls, writer: csv.writer, pays: list[CreditCardPayment]) -> None:
        for pay in sorted(pays, key=lambda p: (p.card_id, p.paid_on, p.payment_id)):
            writer.writerow(cls._payment_row(pay))

    @classmethod
    def _payment_row(cls, pay: CreditCardPayment) -> list[str]:
        return [
            cls.ROW_PAYMENT,
            pay.payment_id,
            pay.card_id,
            "",
            pay.paid_on,
            cls._amount_cell(pay.amount_cop),
            "",
            pay.notes,
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
        ]

    @classmethod
    def _amount_cell(cls, amount: float) -> str:
        return str(int(round(amount)))

    @classmethod
    def from_csv_text(
        cls,
        text: str,
    ) -> tuple[
        list[CreditCard],
        list[CreditCardCategory],
        list[CreditCardExpense],
        list[CreditCardPayment],
    ]:
        """Parse CSV body into the four parallel lists."""
        body = cls._read_body(text)
        cards = [cls._card_from_row(r) for r in body if cls._kind(r) == cls.ROW_CARD]
        cats = [cls._category_from_row(r) for r in body if cls._kind(r) == cls.ROW_CATEGORY]
        exps = [cls._expense_from_row(r) for r in body if cls._kind(r) == cls.ROW_EXPENSE]
        pays = [cls._payment_from_row(r) for r in body if cls._kind(r) == cls.ROW_PAYMENT]
        return cards, cats, exps, pays

    @classmethod
    def _read_body(cls, text: str) -> list[list[str]]:
        reader = csv.reader(io.StringIO(text))
        rows = list(reader)
        if rows and rows[0] == cls.HEADER:
            return rows[1:]
        return rows

    @classmethod
    def _card_from_row(cls, row: list[str]) -> CreditCard:
        return CreditCard(
            card_id=cls._cell(row, 1),
            name=cls._cell(row, 6),
            limit_cop=cls._parse_amount(cls._cell(row, 5)),
            cut_day=cls._parse_int(cls._cell(row, 9), default=1),
            payment_due_day=cls._parse_int(cls._cell(row, 10), default=1),
            color=cls._cell(row, 8),
        )

    @classmethod
    def _category_from_row(cls, row: list[str]) -> CreditCardCategory:
        return CreditCardCategory(
            category_id=cls._cell(row, 1),
            card_id=cls._cell(row, 2),
            title=cls._cell(row, 6),
            color=cls._cell(row, 8),
            linked_label_id=cls._cell(row, 7),
        )

    @classmethod
    def _expense_from_row(cls, row: list[str]) -> CreditCardExpense:
        return CreditCardExpense(
            expense_id=cls._cell(row, 1),
            card_id=cls._cell(row, 2),
            category_id=cls._cell(row, 3),
            occurred_on=cls._cell(row, 4),
            amount_cop=cls._parse_amount(cls._cell(row, 5)),
            description=cls._cell(row, 6),
            installments=cls._parse_int(cls._cell(row, 11), default=1),
            notes=cls._cell(row, 7),
            total_amount_cop=cls._parse_amount(cls._cell(row, 12)),
            installment_number=cls._parse_int(cls._cell(row, 13), default=1),
            parent_expense_id=cls._cell(row, 14),
            entry_order=cls._parse_int(cls._cell(row, 15), default=1),
        )

    @classmethod
    def _payment_from_row(cls, row: list[str]) -> CreditCardPayment:
        return CreditCardPayment(
            payment_id=cls._cell(row, 1),
            card_id=cls._cell(row, 2),
            paid_on=cls._cell(row, 4),
            amount_cop=cls._parse_amount(cls._cell(row, 5)),
            notes=cls._cell(row, 7),
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

    @classmethod
    def _parse_int(cls, raw: str, default: int) -> int:
        if raw == "":
            return default
        try:
            return int(raw)
        except ValueError:
            return default
