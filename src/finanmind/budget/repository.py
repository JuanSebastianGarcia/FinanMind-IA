"""Reads and writes ``budget.csv`` for the configured workspace."""

from __future__ import annotations

import os
from pathlib import Path

from finanmind.budget.csv_codec import BudgetCsvCodec
from finanmind.models.budget_workspace import BudgetWorkspace


class BudgetRepository:
    """Persists budget rows as one CSV file outside the executable bundle."""

    def __init__(self, csv_path: Path) -> None:
        self._csv_path = csv_path

    def load_workspace(self) -> BudgetWorkspace:
        """Return persisted workspace or empty defaults when missing."""
        if not self._csv_path.is_file():
            return BudgetWorkspace(salary_cop=0.0, categories=[])
        raw = self._csv_path.read_text(encoding="utf-8-sig")
        if raw.strip() == "":
            return BudgetWorkspace(salary_cop=0.0, categories=[])
        return BudgetCsvCodec.from_csv_text(raw)

    def save_workspace(self, workspace: BudgetWorkspace) -> None:
        """Atomically replace CSV contents."""
        self._csv_path.parent.mkdir(parents=True, exist_ok=True)
        payload = BudgetCsvCodec.to_csv_text(workspace)
        tmp_path = self._csv_path.with_suffix(".csv.tmp")
        tmp_path.write_text(payload, encoding="utf-8-sig", newline="")
        os.replace(tmp_path, self._csv_path)
