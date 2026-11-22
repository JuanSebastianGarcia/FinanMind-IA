"""High-level adapter from the JavaScript layer to RecurringPaymentService."""

from __future__ import annotations

from datetime import date

from finanmind.budget.book_service import BudgetBookService
from finanmind.services.external_sync_policy import ExternalSyncPolicy
from finanmind.services.google_calendar_auth import GoogleCalendarAuth, GoogleCalendarAuthError
from finanmind.services.google_calendar_client import GoogleCalendarApiError
from finanmind.services.payment_calendar_sync import PaymentCalendarSync
from finanmind.services.recurring_payment_service import RecurringPaymentService
from finanmind.ui.web.bridges.distribution_label_options_builder import DistributionLabelOptionsBuilder
from finanmind.ui.web.bridges.payments_draft_parser import PaymentsDraftParser
from finanmind.ui.web.bridges.payments_state_builder import PaymentsStateBuilder


class PaymentsBridge:
    """Translates JS commands for the Calendario de pagos panel (bills + Google Calendar)."""

    def __init__(self, book: BudgetBookService, service: RecurringPaymentService) -> None:
        self._book = book
        self._service = service
        self._calendar = PaymentCalendarSync(service, enabled=ExternalSyncPolicy.is_enabled())

    def get_state(self, preferred_month: str) -> dict:
        """Snapshot for ``yyyy-mm`` (defaults to the current month)."""
        state = PaymentsStateBuilder.build(self._book, self._service, preferred_month or "", date.today())
        state["google"] = self._calendar.status()
        return state

    def label_options(self) -> list[dict]:
        """``Category · Label`` choices for the payment dialog."""
        return DistributionLabelOptionsBuilder.build(self._book.peek())

    def add_payment(self, data: dict) -> dict:
        """Create a bill (and its calendar event) and return its id plus any calendar warning."""
        pay = self._service.add_payment(PaymentsDraftParser.parse(data), self._book.peek())
        warning = self._calendar.push(pay, self._captions().get(pay.label_id, ""))
        return {"payment_id": pay.payment_id, "calendar_warning": warning}

    def update_payment(self, payment_id: str, data: dict) -> dict:
        """Edit a bill definition and refresh its calendar event."""
        pay = self._service.update_payment(payment_id, PaymentsDraftParser.parse(data), self._book.peek())
        return {"calendar_warning": self._calendar.push(pay, self._captions().get(pay.label_id, ""))}

    def delete_payment(self, payment_id: str) -> dict:
        """Remove a bill, its monthly history and its calendar event."""
        pay = self._service.payment_by_id(payment_id)
        self._service.delete_payment(payment_id)
        return {"calendar_warning": self._calendar.remove(pay)}

    def set_paid(self, payment_id: str, month: str, paid: bool) -> None:
        """Toggle the paid mark of one bill in one month."""
        self._service.set_paid(payment_id, month, bool(paid), date.today())

    def record_amount(self, payment_id: str, month: str, amount, mark_paid: bool) -> None:
        """Register the real value of a variable bill for one month."""
        self._service.record_amount(
            payment_id, month, PaymentsDraftParser.amount(amount), bool(mark_paid), date.today(),
        )

    def google_status(self) -> dict:
        return self._calendar.status()

    def save_google_client(self, json_text: str) -> dict:
        """Store the OAuth desktop client file chosen in the dialog."""
        self._guard(self._calendar.ensure_enabled)
        self._guard(lambda: GoogleCalendarAuth.save_client_from_text(json_text))
        return self._calendar.status()

    def connect_google(self) -> dict:
        """Run the browser consent, then push every bill to the calendar."""
        self._guard(self._calendar.ensure_enabled)
        self._guard(GoogleCalendarAuth.connect)
        result = self.sync_google()
        result["status"] = self._calendar.status()
        return result

    def sync_google(self) -> dict:
        """Push every bill and flush queued deletions."""
        self._guard(self._calendar.ensure_enabled)
        report = self._guard(lambda: self._calendar.sync_all(self._captions()))
        return {"synced": report.synced, "removed": report.removed, "errors": report.errors or []}

    def disconnect_google(self) -> dict:
        """Revoke access; events already created stay in the calendar."""
        self._guard(self._calendar.ensure_enabled)
        GoogleCalendarAuth.disconnect()
        self._calendar.forget_event_ids()
        return self._calendar.status()

    def _captions(self) -> dict[str, str]:
        return {o["label_id"]: o["caption"] for o in DistributionLabelOptionsBuilder.build(self._book.peek())}

    @classmethod
    def _guard(cls, operation):
        """Surface Google errors to JS as plain ``ValueError`` messages."""
        try:
            return operation()
        except (GoogleCalendarAuthError, GoogleCalendarApiError) as exc:
            raise ValueError(str(exc)) from exc
