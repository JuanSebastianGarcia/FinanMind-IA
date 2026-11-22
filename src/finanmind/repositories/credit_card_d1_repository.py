"""Credit cards persisted in Cloudflare D1 (production backend of ``CreditCardRepository``)."""

from __future__ import annotations

from finanmind.models.credit_card import CreditCard
from finanmind.models.credit_card_category import CreditCardCategory
from finanmind.models.credit_card_expense import CreditCardExpense
from finanmind.models.credit_card_payment import CreditCardPayment
from finanmind.storage.d1_client import D1Client
from finanmind.storage.d1_table_sync import D1Table, D1TableSync, Row


class CreditCardD1Repository:
    """Same contract as ``CreditCardRepository`` (``load_all`` / ``save_all``).

    The four tables are owned by this repository, so references between them are
    resolved here before writing: rows of a card that is not being saved are dropped
    (D1 would cascade them anyway) and an expense pointing to a category or parent
    expense that is not being saved gets an empty reference. That keeps every save
    valid regardless of row order, and the snapshot equal to what D1 stores.
    """

    CARDS = D1Table(
        "credit_cards",
        ("card_id",),
        ("card_id", "name", "limit_cop", "cut_day", "payment_due_day", "color"),
        order_by="name, card_id",
    )
    CATEGORIES = D1Table(
        "credit_card_categories",
        ("category_id",),
        ("category_id", "card_id", "title", "color", "linked_label_id"),
        soft_refs={"linked_label_id": "budget_labels.label_id"},
        order_by="card_id, title, category_id",
    )
    EXPENSES = D1Table(
        "credit_card_expenses",
        ("expense_id",),
        (
            "expense_id",
            "card_id",
            "category_id",
            "occurred_on",
            "amount_cop",
            "total_amount_cop",
            "installments",
            "installment_number",
            "parent_expense_id",
            "entry_order",
            "description",
            "notes",
        ),
        order_by="card_id, occurred_on, expense_id",
    )
    PAYMENTS = D1Table(
        "credit_card_payments",
        ("payment_id",),
        ("payment_id", "card_id", "paid_on", "amount_cop", "notes"),
        order_by="card_id, paid_on, payment_id",
    )

    def __init__(self, client: D1Client) -> None:
        self._client = client
        self._cards = D1TableSync(self.CARDS)
        self._categories = D1TableSync(self.CATEGORIES)
        self._expenses = D1TableSync(self.EXPENSES)
        self._payments = D1TableSync(self.PAYMENTS)

    def load_all(
        self,
    ) -> tuple[
        list[CreditCard],
        list[CreditCardCategory],
        list[CreditCardExpense],
        list[CreditCardPayment],
    ]:
        """Return the four parallel lists, sorted like the CSV codec writes them."""
        card_rows, category_rows, expense_rows, payment_rows = D1TableSync.read(
            self._client, [self._cards, self._categories, self._expenses, self._payments]
        )
        return (
            [_CardRows.to_model(r) for r in card_rows],
            [_CategoryRows.to_model(r) for r in category_rows],
            [_ExpenseRows.to_model(r) for r in expense_rows],
            [_PaymentRows.to_model(r) for r in payment_rows],
        )

    def save_all(
        self,
        cards: list[CreditCard],
        categories: list[CreditCardCategory],
        expenses: list[CreditCardExpense],
        payments: list[CreditCardPayment],
    ) -> None:
        """Make the four tables equal the given lists in one atomic batch."""
        card_ids = {c.card_id for c in cards}
        kept_categories = [c for c in categories if c.card_id in card_ids]
        kept_expenses = [e for e in expenses if e.card_id in card_ids]
        category_ids = {c.category_id for c in kept_categories}
        expense_ids = {e.expense_id for e in kept_expenses}
        D1TableSync.write(
            self._client,
            [
                (self._cards, [_CardRows.to_row(c) for c in cards]),
                (self._categories, [_CategoryRows.to_row(c) for c in kept_categories]),
                (self._expenses, [_ExpenseRows.to_row(e, category_ids, expense_ids) for e in kept_expenses]),
                (self._payments, [_PaymentRows.to_row(p) for p in payments if p.card_id in card_ids]),
            ],
        )


class _CardRows:
    @staticmethod
    def to_row(card: CreditCard) -> Row:
        return {
            "card_id": card.card_id,
            "name": card.name,
            "limit_cop": _cop(card.limit_cop),
            "cut_day": int(card.cut_day),
            "payment_due_day": int(card.payment_due_day),
            "color": card.color,
        }

    @staticmethod
    def to_model(r: Row) -> CreditCard:
        return CreditCard(
            card_id=r["card_id"],
            name=r["name"],
            limit_cop=float(r["limit_cop"]),
            cut_day=int(r["cut_day"]),
            payment_due_day=int(r["payment_due_day"]),
            color=r["color"],
        )


class _CategoryRows:
    @staticmethod
    def to_row(cat: CreditCardCategory) -> Row:
        return {
            "category_id": cat.category_id,
            "card_id": cat.card_id,
            "title": cat.title,
            "color": cat.color,
            "linked_label_id": _ref(cat.linked_label_id),
        }

    @staticmethod
    def to_model(r: Row) -> CreditCardCategory:
        return CreditCardCategory(
            category_id=r["category_id"],
            card_id=r["card_id"],
            title=r["title"],
            color=r["color"],
            linked_label_id=r["linked_label_id"] or "",
        )


class _ExpenseRows:
    @staticmethod
    def to_row(ex: CreditCardExpense, category_ids: set[str], expense_ids: set[str]) -> Row:
        # Same-repository references are kept only when their target is saved too;
        # a dangling id would make the whole batch fail its deferred FK check.
        category = ex.category_id if ex.category_id in category_ids else ""
        parent = ex.parent_expense_id if ex.parent_expense_id in expense_ids else ""
        return {
            "expense_id": ex.expense_id,
            "card_id": ex.card_id,
            "category_id": _ref(category),
            "occurred_on": ex.occurred_on,
            "amount_cop": _cop(ex.amount_cop),
            "total_amount_cop": _cop(ex.total_amount_cop),
            "installments": int(ex.installments),
            "installment_number": int(ex.installment_number),
            "parent_expense_id": _ref(parent),
            "entry_order": int(ex.entry_order),
            "description": ex.description,
            "notes": ex.notes,
        }

    @staticmethod
    def to_model(r: Row) -> CreditCardExpense:
        return CreditCardExpense(
            expense_id=r["expense_id"],
            card_id=r["card_id"],
            category_id=r["category_id"] or "",
            occurred_on=r["occurred_on"],
            amount_cop=float(r["amount_cop"]),
            description=r["description"],
            installments=int(r["installments"]),
            notes=r["notes"],
            total_amount_cop=float(r["total_amount_cop"]),
            installment_number=int(r["installment_number"]),
            parent_expense_id=r["parent_expense_id"] or "",
            entry_order=int(r["entry_order"]),
        )


class _PaymentRows:
    @staticmethod
    def to_row(pay: CreditCardPayment) -> Row:
        return {
            "payment_id": pay.payment_id,
            "card_id": pay.card_id,
            "paid_on": pay.paid_on,
            "amount_cop": _cop(pay.amount_cop),
            "notes": pay.notes,
        }

    @staticmethod
    def to_model(r: Row) -> CreditCardPayment:
        return CreditCardPayment(
            payment_id=r["payment_id"],
            card_id=r["card_id"],
            paid_on=r["paid_on"],
            amount_cop=float(r["amount_cop"]),
            notes=r["notes"],
        )


def _ref(value: str) -> str | None:
    """Models use ``""`` for an empty reference; D1 stores NULL."""
    return value or None


def _cop(amount: float) -> int:
    """COP amounts are stored as whole pesos, like the CSV codec does."""
    return int(round(amount))
