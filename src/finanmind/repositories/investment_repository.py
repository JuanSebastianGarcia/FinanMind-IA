"""Atomic persistence for the unified investments CSV workspace file."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from finanmind.models.investment_category import InvestmentCategory
from finanmind.models.investment_entry import InvestmentEntry
from finanmind.repositories.investment_csv_codec import InvestmentCsvCodec


class InvestmentRepository:
    """Reads and writes categories and holdings in one CSV path."""

    def __init__(self, csv_path: Path) -> None:
        self._csv_path = csv_path
        self._log = logging.getLogger(__name__)

    def load_all(self) -> tuple[list[InvestmentCategory], list[InvestmentEntry]]:
        """Return empty lists when the CSV is missing or blank."""
        if not self._csv_path.is_file():
            return [], []
        raw = self._csv_path.read_text(encoding="utf-8-sig")
        if raw.strip() == "":
            return [], []
        return InvestmentCsvCodec.from_csv_text(raw)

    def save_all(self, categories: list[InvestmentCategory], entries: list[InvestmentEntry]) -> None:
        """Replace CSV contents atomically."""
        self._csv_path.parent.mkdir(parents=True, exist_ok=True)
        payload = InvestmentCsvCodec.to_csv_text(categories, entries)
        tmp_path = self._csv_path.with_suffix(".csv.tmp")
        tmp_path.write_text(payload, encoding="utf-8-sig", newline="")
        os.replace(tmp_path, self._csv_path)
        self._log.debug("Saved investments CSV at %s", self._csv_path)
