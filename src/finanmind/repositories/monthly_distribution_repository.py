"""Persist income receipts and distribution lines as one CSV."""

from __future__ import annotations

import os
from pathlib import Path

from finanmind.models.income_distribution_line import IncomeDistributionLine
from finanmind.models.income_receipt import IncomeReceipt
from finanmind.repositories.monthly_distribution_csv_codec import MonthlyDistributionCsvCodec


class MonthlyDistributionRepository:
    """Atomic read/write for distribution ledger CSV."""

    def __init__(self, csv_path: Path) -> None:
        self._csv_path = csv_path

    def load_all(self) -> tuple[list[IncomeReceipt], list[IncomeDistributionLine]]:
        """Return empty lists when the file is missing."""
        if not self._csv_path.is_file():
            return [], []
        raw = self._csv_path.read_text(encoding="utf-8-sig")
        if raw.strip() == "":
            return [], []
        return MonthlyDistributionCsvCodec.from_csv_text(raw)

    def save_all(
        self,
        receipts: list[IncomeReceipt],
        lines: list[IncomeDistributionLine],
    ) -> None:
        """Replace CSV contents atomically."""
        self._csv_path.parent.mkdir(parents=True, exist_ok=True)
        payload = MonthlyDistributionCsvCodec.to_csv_text(receipts, lines)
        tmp_path = self._csv_path.with_suffix(".csv.tmp")
        tmp_path.write_text(payload, encoding="utf-8-sig", newline="")
        os.replace(tmp_path, self._csv_path)
