"""CRUD plus query helpers for credit cards, categories, expenses, and payments."""

from __future__ import annotations

import calendar
import uuid

from finanmind.models.credit_card import CreditCard
from finanmind.models.credit_card_category import CreditCardCategory
from finanmind.models.credit_card_expense import CreditCardExpense
from finanmind.models.credit_card_payment import CreditCardPayment
from finanmind.repositories.credit_card_repository import CreditCardRepository


class CreditCardService:
    """In-memory store backed by ``CreditCardRepository`` with persistence on every mutation."""

    def __init__(self, repository: CreditCardRepository) -> None:
        self._repository = repository
        self._cards: list[CreditCard] = []
        self._categories: list[CreditCardCategory] = []
        self._expenses: list[CreditCardExpense] = []
        self._payments: list[CreditCardPayment] = []

    def load(self) -> None:
        """Reload all four lists from disk."""
        cards, cats, exps, pays = self._repository.load_all()
        self._cards = cards
        self._categories = cats
        self._expenses = exps
        self._payments = pays

    def persist(self) -> None:
        """Flush in-memory data."""
        self._repository.save_all(self._cards, self._categories, self._expenses, self._payments)

    def cards_snapshot(self) -> list[CreditCard]:
        """Read-only copy of all cards."""
        return list(self._cards)

    def expenses_snapshot(self) -> list[CreditCardExpense]:
        """Shallow copy of every expense for reporting dashboards."""
        return list(self._expenses)

    def card_by_id(self, card_id: str) -> CreditCard:
        """Return card or raise KeyError."""
        for card in self._cards:
            if card.card_id == card_id:
                return card
        raise KeyError("Tarjeta no encontrada")

    def add_card(
        self,
        name: str,
        limit_cop: float,
        cut_day: int,
        payment_due_day: int,
        color: str,
    ) -> CreditCard:
        """Insert a new card after validating the cycle days."""
        clean_name = self._require_text(name, "Nombre requerido")
        self._assert_positive(limit_cop)
        self._assert_day(cut_day)
        self._assert_day(payment_due_day)
        card = CreditCard(
            card_id=str(uuid.uuid4()),
            name=clean_name,
            limit_cop=limit_cop,
            cut_day=cut_day,
            payment_due_day=payment_due_day,
            color=color.strip(),
        )
        self._cards.append(card)
        self.persist()
        return card

    def update_card(
        self,
        card_id: str,
        name: str,
        limit_cop: float,
        cut_day: int,
        payment_due_day: int,
        color: str,
    ) -> CreditCard:
        """Mutate an existing card in place."""
        card = self.card_by_id(card_id)
        card.name = self._require_text(name, "Nombre requerido")
        self._assert_positive(limit_cop)
        self._assert_day(cut_day)
        self._assert_day(payment_due_day)
        card.limit_cop = limit_cop
        card.cut_day = cut_day
        card.payment_due_day = payment_due_day
        card.color = color.strip()
        self.persist()
        return card

    def delete_card(self, card_id: str) -> None:
        """Remove the card and every category, expense, and payment that references it."""
        before = len(self._cards)
        self._cards = [c for c in self._cards if c.card_id != card_id]
        if len(self._cards) == before:
            raise KeyError("Tarjeta no encontrada")
        self._categories = [c for c in self._categories if c.card_id != card_id]
        self._expenses = [e for e in self._expenses if e.card_id != card_id]
        self._payments = [p for p in self._payments if p.card_id != card_id]
        self.persist()

    def categories_for_card(self, card_id: str) -> list[CreditCardCategory]:
        """Return categories owned by a card sorted by title."""
        bucket = [c for c in self._categories if c.card_id == card_id]
        return sorted(bucket, key=lambda c: c.title.lower())

    def category_by_id(self, category_id: str) -> CreditCardCategory:
        """Return category or raise KeyError."""
        for cat in self._categories:
            if cat.category_id == category_id:
                return cat
        raise KeyError("Categoría no encontrada")

    def add_category(
        self,
        card_id: str,
        title: str,
        color: str,
        linked_label_id: str = "",
    ) -> CreditCardCategory:
        """Insert a new category bound to a card; optionally link to a budget label."""
        self.card_by_id(card_id)
        clean_title = self._require_text(title, "Título requerido")
        link_id = linked_label_id.strip()
        self._clear_link_on_other_categories(link_id, keep_id="")
        cat = CreditCardCategory(
            category_id=str(uuid.uuid4()),
            card_id=card_id,
            title=clean_title,
            color=color.strip(),
            linked_label_id=link_id,
        )
        self._categories.append(cat)
        self.persist()
        return cat

    def update_category(
        self,
        category_id: str,
        title: str,
        color: str,
        linked_label_id: str = "",
    ) -> CreditCardCategory:
        """Mutate title, color, and the optional budget-label link in place."""
        cat = self.category_by_id(category_id)
        cat.title = self._require_text(title, "Título requerido")
        cat.color = color.strip()
        link_id = linked_label_id.strip()
        self._clear_link_on_other_categories(link_id, keep_id=category_id)
        cat.linked_label_id = link_id
        self.persist()
        return cat

    def delete_category(self, category_id: str) -> None:
        """Remove the category and clear it from existing expenses."""
        before = len(self._categories)
        self._categories = [c for c in self._categories if c.category_id != category_id]
        if len(self._categories) == before:
            raise KeyError("Categoría no encontrada")
        for ex in self._expenses:
            if ex.category_id == category_id:
                ex.category_id = ""
        self.persist()

    def set_link_for_label(self, label_id: str, target_category_id: str) -> None:
        """Make ``target_category_id`` the unique CC category linked to ``label_id``."""
        label_token = label_id.strip()
        target = target_category_id.strip()
        if label_token == "":
            return
        self._clear_link_on_other_categories(label_token, keep_id=target)
        if target != "":
            cat = self.category_by_id(target)
            cat.linked_label_id = label_token
        self.persist()

    def category_for_label(self, label_id: str) -> CreditCardCategory | None:
        """Return the single CC category linked to ``label_id`` or None."""
        token = label_id.strip()
        if token == "":
            return None
        for cat in self._categories:
            if cat.linked_label_id == token:
                return cat
        return None

    def card_for_category(self, category_id: str) -> CreditCard | None:
        """Return the parent card of a category or None."""
        try:
            cat = self.category_by_id(category_id)
        except KeyError:
            return None
        try:
            return self.card_by_id(cat.card_id)
        except KeyError:
            return None

    def _clear_link_on_other_categories(self, label_id: str, keep_id: str) -> None:
        if label_id == "":
            return
        for cat in self._categories:
            if cat.category_id == keep_id:
                continue
            if cat.linked_label_id == label_id:
                cat.linked_label_id = ""

    def expenses_for_card(self, card_id: str) -> list[CreditCardExpense]:
        """Return all expenses for the card sorted by month, entry_order, then date."""
        bucket = [e for e in self._expenses if e.card_id == card_id]
        return sorted(bucket, key=lambda e: (e.occurred_on[:7], e.entry_order, e.occurred_on, e.expense_id))

    def expense_by_id(self, expense_id: str) -> CreditCardExpense:
        """Return expense or raise KeyError."""
        for ex in self._expenses:
            if ex.expense_id == expense_id:
                return ex
        raise KeyError("Gasto no encontrado")

    def add_expense(
        self,
        card_id: str,
        category_id: str,
        occurred_on: str,
        total_amount_cop: float,
        description: str,
        installments: int,
        notes: str,
    ) -> CreditCardExpense:
        """Append one or more charges.

        For ``installments > 1`` the purchase is spread across consecutive months:
        the first record keeps the original date and description; subsequent records
        are placed one month apart and labelled "Cuota X/N de <description>".
        """
        self.card_by_id(card_id)
        self._validate_expense_inputs(total_amount_cop, occurred_on, installments)

        n = int(installments)
        cuota = round(total_amount_cop / n) if n > 1 else total_amount_cop
        clean_cat = category_id.strip()
        clean_desc = description.strip()
        clean_notes = notes.strip()
        clean_date = occurred_on.strip()

        first_order = self._next_entry_order(card_id, clean_date[:7])
        first = CreditCardExpense(
            expense_id=str(uuid.uuid4()),
            card_id=card_id,
            category_id=clean_cat,
            occurred_on=clean_date,
            amount_cop=cuota,
            description=clean_desc,
            installments=n,
            notes=clean_notes,
            total_amount_cop=total_amount_cop if n > 1 else 0.0,
            installment_number=1,
            parent_expense_id="",
            entry_order=first_order,
        )
        self._expenses.append(first)

        for i in range(2, n + 1):
            future_date = self._advance_months(clean_date, i - 1)
            child = CreditCardExpense(
                expense_id=str(uuid.uuid4()),
                card_id=card_id,
                category_id=clean_cat,
                occurred_on=future_date,
                amount_cop=cuota,
                description=f"Cuota {i}/{n} de {clean_desc}",
                installments=n,
                notes=clean_notes,
                total_amount_cop=total_amount_cop,
                installment_number=i,
                parent_expense_id=first.expense_id,
                entry_order=self._next_entry_order(card_id, future_date[:7]),
            )
            self._expenses.append(child)

        self.persist()
        return first

    def update_expense(
        self,
        expense_id: str,
        category_id: str,
        occurred_on: str,
        total_amount_cop: float,
        description: str,
        notes: str,
    ) -> CreditCardExpense:
        """Mutate an expense in place.

        For child installments (installment_number > 1) the amount is locked;
        only category, date, description and notes are updated.
        """
        ex = self.expense_by_id(expense_id)
        self._require_iso_day(occurred_on.strip())
        self._assert_positive(total_amount_cop)

        ex.category_id = category_id.strip()
        ex.occurred_on = occurred_on.strip()
        ex.description = description.strip()
        ex.notes = notes.strip()

        if ex.installment_number == 1:
            n = ex.installments
            ex.amount_cop = round(total_amount_cop / n) if n > 1 else total_amount_cop
            if n > 1:
                ex.total_amount_cop = total_amount_cop

        self.persist()
        return ex

    def delete_expense(self, expense_id: str) -> None:
        """Remove an expense.

        If the target is the first installment of a multi-installment series,
        all child installments are also removed.
        """
        target = self.expense_by_id(expense_id)
        to_remove = {expense_id}
        if target.installment_number == 1 and target.installments > 1:
            for ex in self._expenses:
                if ex.parent_expense_id == expense_id:
                    to_remove.add(ex.expense_id)
        before = len(self._expenses)
        self._expenses = [e for e in self._expenses if e.expense_id not in to_remove]
        if len(self._expenses) == before:
            raise KeyError("Gasto no encontrado")
        self.persist()

    def payments_for_card(self, card_id: str) -> list[CreditCardPayment]:
        """Return payments for the card sorted by date asc, id asc."""
        bucket = [p for p in self._payments if p.card_id == card_id]
        return sorted(bucket, key=lambda p: (p.paid_on, p.payment_id))

    def add_payment(
        self,
        card_id: str,
        paid_on: str,
        amount_cop: float,
        notes: str,
    ) -> CreditCardPayment:
        """Append a new payment after validating fields."""
        self.card_by_id(card_id)
        self._assert_positive(amount_cop)
        self._require_iso_day(paid_on)
        pay = CreditCardPayment(
            payment_id=str(uuid.uuid4()),
            card_id=card_id,
            paid_on=paid_on.strip(),
            amount_cop=amount_cop,
            notes=notes.strip(),
        )
        self._payments.append(pay)
        self.persist()
        return pay

    def delete_payment(self, payment_id: str) -> None:
        """Remove a single payment."""
        before = len(self._payments)
        self._payments = [p for p in self._payments if p.payment_id != payment_id]
        if len(self._payments) == before:
            raise KeyError("Pago no encontrado")
        self.persist()

    def expenses_in_range(
        self,
        card_id: str,
        start_iso: str,
        end_iso: str,
    ) -> list[CreditCardExpense]:
        """Filter expenses for card whose date is in the inclusive [start, end] range."""
        bucket = self.expenses_for_card(card_id)
        return [e for e in bucket if start_iso <= e.occurred_on <= end_iso]

    def known_expense_months(self, card_id: str) -> list[str]:
        """Distinct ``yyyy-mm`` from expenses for a card, newest first."""
        tokens: set[str] = set()
        for ex in self._expenses:
            if ex.card_id != card_id:
                continue
            if len(ex.occurred_on) >= 7:
                tokens.add(ex.occurred_on[:7])
        return sorted(tokens, reverse=True)

    def _next_entry_order(self, card_id: str, month_prefix: str) -> int:
        """Return the next sequential order number for expenses within a given month."""
        orders = [
            e.entry_order
            for e in self._expenses
            if e.card_id == card_id and e.occurred_on[:7] == month_prefix
        ]
        return max(orders, default=0) + 1

    @staticmethod
    def _advance_months(date_iso: str, months: int) -> str:
        """Return an ISO date string advanced by the given number of months."""
        year = int(date_iso[:4])
        month = int(date_iso[5:7])
        day = int(date_iso[8:10])
        total = (year * 12 + month - 1) + months
        new_year = total // 12
        new_month = (total % 12) + 1
        new_day = min(day, calendar.monthrange(new_year, new_month)[1])
        return f"{new_year:04d}-{new_month:02d}-{new_day:02d}"

    def _validate_expense_inputs(self, amount_cop: float, day: str, installments: int) -> None:
        self._assert_positive(amount_cop)
        self._require_iso_day(day)
        if int(installments) < 1:
            raise ValueError("Las cuotas deben ser un entero positivo")

    def _assert_positive(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("El monto debe ser mayor que cero")

    def _assert_day(self, day: int) -> None:
        if not 1 <= int(day) <= 31:
            raise ValueError("El día debe estar entre 1 y 31")

    def _require_text(self, raw: str, error: str) -> str:
        cleaned = raw.strip()
        if cleaned == "":
            raise ValueError(error)
        return cleaned

    def _require_iso_day(self, raw: str) -> str:
        day = raw.strip()
        if len(day) != 10 or day[4] != "-" or day[7] != "-":
            raise ValueError("Usa la fecha en formato AAAA-MM-DD")
        return day
