"""Persist credit cards and their dependent rows in one CSV file."""

from __future__ import annotations

import os
from pathlib import Path

from finanmind.models.credit_card import CreditCard
from finanmind.models.credit_card_category import CreditCardCategory
from finanmind.models.credit_card_expense import CreditCardExpense
from finanmind.models.credit_card_payment import CreditCardPayment
from finanmind.repositories.credit_card_csv_codec import CreditCardCsvCodec


class CreditCardRepository:
    """Atomic read/write for the unified credit-cards CSV."""

    def __init__(self, csv_path: Path) -> None:
        self._csv_path = csv_path

    def load_all(
        self,
    ) -> tuple[
        list[CreditCard],
        list[CreditCardCategory],
        list[CreditCardExpense],
        list[CreditCardPayment],
    ]:
        """Return empty lists when the CSV is missing or empty."""
        if not self._csv_path.is_file():
            return [], [], [], []
        raw = self._csv_path.read_text(encoding="utf-8-sig")
        if raw.strip() == "":
            return [], [], [], []
        return CreditCardCsvCodec.from_csv_text(raw)

    def save_all(
        self,
        cards: list[CreditCard],
        categories: list[CreditCardCategory],
        expenses: list[CreditCardExpense],
        payments: list[CreditCardPayment],
    ) -> None:
        """Replace CSV contents atomically."""
        self._csv_path.parent.mkdir(parents=True, exist_ok=True)
        payload = CreditCardCsvCodec.to_csv_text(cards, categories, expenses, payments)
        tmp_path = self._csv_path.with_suffix(".csv.tmp")
        tmp_path.write_text(payload, encoding="utf-8-sig", newline="")
        os.replace(tmp_path, self._csv_path)
