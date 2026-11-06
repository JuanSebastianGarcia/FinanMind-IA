"""Writes parsed NU statement transactions to a CSV file under the user workspace."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from finanmind.config import AppConfig

_FIELDNAMES = [
    "occurred_on",
    "description",
    "value",
    "installments",
    "monthly_value",
    "interest_pct",
    "interest_value",
    "total_this_month",
    "remaining",
]


class NuExpenseCsvWriter:
    """Persists one CSV per extraction run, under ``nu_statement_imports/<card_id>/``."""

    SUBDIR = "nu_statement_imports"

    @classmethod
    def write(cls, card_id: str, rows: list[dict]) -> str:
        """Write ``rows`` to a timestamped CSV file and return its path."""
        root = AppConfig.USER_DATA_ROOT
        if root is None:
            raise RuntimeError("Workspace folder not configured yet.")
        folder = Path(root) / cls.SUBDIR / card_id
        folder.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = folder / f"extracto_{stamp}.csv"
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=_FIELDNAMES)
            writer.writeheader()
            for row in rows:
                writer.writerow({key: row.get(key, "") for key in _FIELDNAMES})
        return str(path)
