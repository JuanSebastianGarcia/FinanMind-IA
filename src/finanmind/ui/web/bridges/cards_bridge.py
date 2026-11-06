"""High-level adapter from the JavaScript layer to the credit-card services."""

from __future__ import annotations

from finanmind.budget.book_service import BudgetBookService
from finanmind.budget.palette import BudgetCategoryPalette
from finanmind.services.credit_card_service import CreditCardService
from finanmind.services.gmail_automation_store import GmailAutomationStore
from finanmind.services.gmail_connection_validator import GmailConnectionValidator
from finanmind.services.known_expense_category_store import KnownExpenseCategoryStore
from finanmind.services.nu_expense_csv_writer import NuExpenseCsvWriter
from finanmind.services.nu_expense_row_interpreter import NuExpenseRowInterpreter
from finanmind.services.nu_pdf_password_store import NuPdfPasswordStore
from finanmind.services.nu_statement_email_scanner import NuStatementEmailScanner
from finanmind.services.nu_statement_pdf_parser import NuPdfWrongPasswordError, NuStatementPdfParser
from finanmind.ui.web.bridges.cards_detail_state_builder import CardsDetailStateBuilder
from finanmind.ui.web.bridges.cards_label_options_builder import CardsLabelOptionsBuilder
from finanmind.ui.web.bridges.cards_tile_payload_builder import CardsTilePayloadBuilder


class CardsBridge:
    """Translates JS commands into ``CreditCardService`` calls."""

    def __init__(self, book: BudgetBookService, cards: CreditCardService) -> None:
        self._book = book
        self._cards = cards

    def dashboard_state(self) -> dict:
        """Return the snapshot used by the cards dashboard grid."""
        return {"cards": CardsTilePayloadBuilder.build_many(self._cards)}

    def detail_state(self, card_id: str, preferred_cycle: str) -> dict:
        """Return the snapshot used by the single-card detail view."""
        return CardsDetailStateBuilder.build(self._cards, self._book, card_id, preferred_cycle or "")

    def label_options(self) -> list[dict]:
        """Return the budget-label options used by the card-category dialog."""
        return CardsLabelOptionsBuilder.build(self._book)

    def palette_presets(self) -> list[str]:
        """Return the colour presets shared with the budget palette."""
        return list(BudgetCategoryPalette.PRESETS)

    def add_card(
        self,
        name: str,
        limit: float,
        cut_day: int,
        payment_due_day: int,
        color: str,
    ) -> dict:
        """Persist a new card and return its identifier for navigation."""
        card = self._cards.add_card(name, float(limit), int(cut_day), int(payment_due_day), color or "")
        return {"card_id": card.card_id}

    def update_card(
        self,
        card_id: str,
        name: str,
        limit: float,
        cut_day: int,
        payment_due_day: int,
        color: str,
    ) -> None:
        """Mutate an existing card in place."""
        self._cards.update_card(card_id, name, float(limit), int(cut_day), int(payment_due_day), color or "")

    def delete_card(self, card_id: str) -> None:
        """Remove a card plus all its categories, expenses and payments."""
        self._cards.delete_card(card_id)

    def add_category(self, card_id: str, title: str, color: str, link_id: str) -> dict:
        """Insert a new category bound to a card and (optional) budget label."""
        cat = self._cards.add_category(card_id, title, color or "", link_id or "")
        return {"category_id": cat.category_id}

    def update_category(self, category_id: str, title: str, color: str, link_id: str) -> None:
        """Edit one card category and (re)apply its budget-label link."""
        self._cards.update_category(category_id, title, color or "", link_id or "")

    def delete_category(self, category_id: str) -> None:
        """Remove one category and clear it from existing expenses."""
        self._cards.delete_category(category_id)

    def add_expense(
        self,
        card_id: str,
        category_id: str,
        occurred_on: str,
        total_amount_cop: float,
        description: str,
        installments: int,
        notes: str,
    ) -> None:
        """Append a new charge for one card. For installments > 1 creates sibling records."""
        self._cards.add_expense(
            card_id, category_id or "", occurred_on, float(total_amount_cop), description, int(installments), notes or "",
        )

    def update_expense(
        self,
        expense_id: str,
        category_id: str,
        occurred_on: str,
        total_amount_cop: float,
        description: str,
        notes: str,
    ) -> None:
        """Mutate an existing charge in place."""
        self._cards.update_expense(
            expense_id, category_id or "", occurred_on, float(total_amount_cop), description, notes or "",
        )

    def delete_expense(self, expense_id: str) -> None:
        """Remove one charge from the card history."""
        self._cards.delete_expense(expense_id)

    def add_payment(self, card_id: str, paid_on: str, amount: float, notes: str) -> None:
        """Register a payment reducing the card debt."""
        self._cards.add_payment(card_id, paid_on, float(amount), notes or "")

    def delete_payment(self, payment_id: str) -> None:
        """Remove one payment from the card history."""
        self._cards.delete_payment(payment_id)

    def automation_state(self, card_id: str) -> dict:
        """Return whether Gmail processing automation is configured for a card."""
        entry = GmailAutomationStore.get(card_id)
        if entry is None:
            return {"configured": False, "email": ""}
        return {"configured": True, "email": entry["email"]}

    def save_automation(self, card_id: str, email: str, app_password: str) -> None:
        """Validate the Gmail IMAP connection and, on success, link it to the card."""
        GmailConnectionValidator.validate(email.strip(), app_password.strip())
        GmailAutomationStore.save(card_id, email, app_password)

    def clear_automation(self, card_id: str) -> None:
        """Unlink the Gmail account used to automate this card's processing."""
        GmailAutomationStore.clear(card_id)

    def scan_statement_emails(self, card_id: str) -> list[dict]:
        """Look up NU statement-arrival emails in the linked Gmail account."""
        credentials = GmailAutomationStore.credentials_for(card_id)
        if credentials is None:
            raise ValueError("Primero conecta la cuenta de Gmail de esta tarjeta.")
        email_address, app_password = credentials
        return NuStatementEmailScanner.scan(email_address, app_password)

    def extract_statement_expenses(
        self,
        card_id: str,
        message_ids: list[str],
        pdf_password: str = "",
    ) -> dict:
        """Download the selected statement PDFs, parse their expense table and save a CSV.

        The PDF password is remembered per card (NU reuses the same one for every
        statement), so ``pdf_password`` only needs to be passed the first time, or
        again after ``PDF_PASSWORD_INVALID``/``PDF_PASSWORD_REQUIRED`` is raised.
        """
        if not message_ids:
            raise ValueError("Selecciona al menos un extracto para continuar.")
        credentials = GmailAutomationStore.credentials_for(card_id)
        if credentials is None:
            raise ValueError("Primero conecta la cuenta de Gmail de esta tarjeta.")
        email_address, app_password = credentials
        pdf_by_message = NuStatementEmailScanner.fetch_pdf_attachments(email_address, app_password, message_ids)

        typed_password = pdf_password.strip()
        password_to_try = typed_password or NuPdfPasswordStore.get(card_id)
        if not password_to_try:
            raise ValueError("PDF_PASSWORD_REQUIRED")

        try:
            rows: list[dict] = []
            for message_id in message_ids:
                rows.extend(NuStatementPdfParser.parse(pdf_by_message[message_id], password_to_try))
        except NuPdfWrongPasswordError as err:
            raise ValueError("PDF_PASSWORD_INVALID") from err

        if typed_password:
            NuPdfPasswordStore.save(card_id, typed_password)

        csv_path = NuExpenseCsvWriter.write(card_id, rows)
        return {"rows": rows, "csv_path": csv_path}

    def card_categories(self, card_id: str) -> list[dict]:
        """Return the categories available on a card, for the auto-registration wizard."""
        return [
            {"category_id": cat.category_id, "title": cat.title, "color": cat.color}
            for cat in self._cards.categories_for_card(card_id)
        ]

    def classify_extracted_expense(self, card_id: str, row: dict) -> dict:
        """Decide how to handle one extracted statement row before registering it.

        Returns ``type`` ("payment" or "expense"), and for expenses whether the
        description is already known (with its category) and whether this exact
        transaction was already registered (to avoid double-booking installments
        that reappear across several monthly statements).
        """
        if not NuExpenseRowInterpreter.is_expense_row(row):
            amount = NuExpenseRowInterpreter.parse_money(row.get("value", ""))
            already_registered = self._payment_already_registered(card_id, row["occurred_on"], amount)
            return {"type": "payment", "already_registered": already_registered}

        current, total = NuExpenseRowInterpreter.parse_installments(row.get("installments", ""))
        if current > 1:
            # Only the first installment triggers registration (it creates every
            # sibling installment at once); later installments of the same plan
            # reappearing on later statements must have been booked back then.
            return {"type": "expense", "skip_not_first_installment": True}

        origin_date = NuExpenseRowInterpreter.origin_date(row["occurred_on"], current)
        amount = NuExpenseRowInterpreter.parse_money(row.get("value", ""))
        description = row.get("description", "").strip()

        category_id = KnownExpenseCategoryStore.lookup(card_id, description)
        already_registered = self._expense_already_registered(card_id, origin_date, amount)
        return {
            "type": "expense",
            "known": category_id is not None,
            "category_id": category_id or "",
            "already_registered": already_registered,
            "origin_date": origin_date,
            "installments_total": total,
            "amount": amount,
        }

    def register_extracted_expense(
        self,
        card_id: str,
        row: dict,
        category_id: str,
        remember: bool,
        description_override: str = "",
    ) -> dict:
        """Register one classified row as a payment or a categorized expense."""
        if not NuExpenseRowInterpreter.is_expense_row(row):
            amount = NuExpenseRowInterpreter.parse_money(row.get("value", ""))
            if self._payment_already_registered(card_id, row["occurred_on"], amount):
                return {"status": "skipped_duplicate"}
            self._cards.add_payment(card_id, row["occurred_on"], amount, row.get("description", ""))
            return {"status": "registered_payment"}

        current, total = NuExpenseRowInterpreter.parse_installments(row.get("installments", ""))
        if current > 1:
            return {"status": "skipped_not_first_installment"}

        origin_date = NuExpenseRowInterpreter.origin_date(row["occurred_on"], current)
        amount = NuExpenseRowInterpreter.parse_money(row.get("value", ""))
        description = row.get("description", "").strip()

        if self._expense_already_registered(card_id, origin_date, amount):
            return {"status": "skipped_duplicate"}

        clean_category = category_id.strip()
        if not clean_category:
            raise ValueError("Selecciona una categoría para registrar este gasto.")

        # The custom label only changes what gets displayed on the ledger; matching
        # future statements against the "known expense" CSV still keys off the
        # original description NU prints, so auto-registration keeps working.
        display_description = description_override.strip() or description
        self._cards.add_expense(card_id, clean_category, origin_date, amount, display_description, total, "")
        if remember:
            KnownExpenseCategoryStore.remember(card_id, description, clean_category)
        return {"status": "registered_expense"}

    def _expense_already_registered(
        self,
        card_id: str,
        origin_date: str,
        amount: float,
    ) -> bool:
        """True when an expense with this exact date + total amount is already on file.

        Compared against each purchase's anchor record (``installment_number == 1``),
        since that is the only sibling that carries the original date and the full
        amount. The merchant description is intentionally not part of the match:
        the same purchase can come back with slightly different wording between
        statements (line-wrap differences), and date+amount alone is what actually
        identifies "the same charge" for NU statements.
        """
        for expense in self._cards.expenses_snapshot():
            if expense.card_id != card_id or expense.installment_number != 1:
                continue
            if expense.occurred_on != origin_date:
                continue
            registered_total = expense.total_amount_cop if expense.installments > 1 else expense.amount_cop
            if abs(registered_total - amount) < 1.0:
                return True
        return False

    def remove_duplicate_expenses(self, card_id: str) -> dict:
        """Emergency cleanup: delete extra expenses AND payments sharing date + amount.

        Groups every purchase's anchor record (``installment_number == 1``) by
        ``(occurred_on, total amount)``; within each group the first one registered
        is kept and the rest (plus their installment siblings) are deleted. Payments
        get the same treatment, grouped by ``(paid_on, amount)``, since the same
        double-registration bug can duplicate a "Gracias por tu pago" row too.
        """
        removed_expenses = self._remove_duplicate_anchor_expenses(card_id)
        removed_payments = self._remove_duplicate_payments(card_id)
        return {"removed": removed_expenses, "removed_payments": removed_payments}

    def _remove_duplicate_anchor_expenses(self, card_id: str) -> int:
        anchors = [
            expense for expense in self._cards.expenses_snapshot()
            if expense.card_id == card_id and expense.installment_number == 1
        ]
        anchors.sort(key=lambda expense: expense.entry_order)

        seen: dict[tuple[str, int], str] = {}
        removed = 0
        for expense in anchors:
            total = expense.total_amount_cop if expense.installments > 1 else expense.amount_cop
            key = (expense.occurred_on, round(total))
            if key in seen:
                self._cards.delete_expense(expense.expense_id)
                removed += 1
            else:
                seen[key] = expense.expense_id
        return removed

    def _remove_duplicate_payments(self, card_id: str) -> int:
        payments = sorted(self._cards.payments_for_card(card_id), key=lambda payment: payment.payment_id)
        seen: dict[tuple[str, int], str] = {}
        removed = 0
        for payment in payments:
            key = (payment.paid_on, round(payment.amount_cop))
            if key in seen:
                self._cards.delete_payment(payment.payment_id)
                removed += 1
            else:
                seen[key] = payment.payment_id
        return removed

    def _payment_already_registered(self, card_id: str, paid_on: str, amount: float) -> bool:
        """Same merchant-less check for payments: same date + same amount already on file."""
        for payment in self._cards.payments_for_card(card_id):
            if payment.paid_on != paid_on:
                continue
            if abs(payment.amount_cop - amount) < 1.0:
                return True
        return False
