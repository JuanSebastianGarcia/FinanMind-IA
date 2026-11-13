"""Persist recurring payments and their monthly status as one CSV."""

from __future__ import annotations

import os
from pathlib import Path

from finanmind.models.recurring_payment import RecurringPayment
from finanmind.models.recurring_payment_month import RecurringPaymentMonth
from finanmind.repositories.recurring_payment_csv_codec import RecurringPaymentCsvCodec


class RecurringPaymentRepository:
    """Atomic read/write for ``recurring_payments.csv``."""

    def __init__(self, csv_path: Path) -> None:
        self._csv_path = csv_path

    def load_all(self) -> tuple[list[RecurringPayment], list[RecurringPaymentMonth]]:
        """Return empty lists when the file is missing or blank."""
        if not self._csv_path.is_file():
            return [], []
        raw = self._csv_path.read_text(encoding="utf-8-sig")
        if raw.strip() == "":
            return [], []
        return RecurringPaymentCsvCodec.from_csv_text(raw)

    def save_all(
        self,
        payments: list[RecurringPayment],
        months: list[RecurringPaymentMonth],
    ) -> None:
        """Replace CSV contents atomically."""
        self._csv_path.parent.mkdir(parents=True, exist_ok=True)
        payload = RecurringPaymentCsvCodec.to_csv_text(payments, months)
        tmp_path = self._csv_path.with_suffix(".csv.tmp")
        tmp_path.write_text(payload, encoding="utf-8-sig", newline="")
        os.replace(tmp_path, self._csv_path)
