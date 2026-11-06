"""Remembers which card category an expense description maps to, per card."""

from __future__ import annotations

import csv
from pathlib import Path

from finanmind.config import AppConfig

_FIELDNAMES = ["card_id", "description_key", "category_id"]


class KnownExpenseCategoryStore:
    """CSV-backed ``(card_id, description) -> category_id`` lookup for NU auto-registration."""

    FILENAME = "known_expense_categories.csv"

    @classmethod
    def lookup(cls, card_id: str, description: str) -> str | None:
        """Return the remembered category id for this description on this card, if any."""
        key = cls._normalize(description)
        for row in cls._read_all():
            if row["card_id"] == card_id and row["description_key"] == key:
                return row["category_id"]
        return None

    @classmethod
    def remember(cls, card_id: str, description: str, category_id: str) -> None:
        """Store (or update) the category this description should map to on this card."""
        key = cls._normalize(description)
        rows = [
            row for row in cls._read_all()
            if not (row["card_id"] == card_id and row["description_key"] == key)
        ]
        rows.append({"card_id": card_id, "description_key": key, "category_id": category_id})
        cls._write_all(rows)

    @classmethod
    def _normalize(cls, description: str) -> str:
        return " ".join(description.strip().lower().split())

    @classmethod
    def _read_all(cls) -> list[dict]:
        try:
            path = cls._path_or_raise()
        except RuntimeError:
            return []
        if not path.is_file():
            return []
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))

    @classmethod
    def _write_all(cls, rows: list[dict]) -> None:
        path = cls._path_or_raise()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=_FIELDNAMES)
            writer.writeheader()
            writer.writerows(rows)

    @classmethod
    def _path_or_raise(cls) -> Path:
        root = AppConfig.USER_DATA_ROOT
        if root is None:
            raise RuntimeError("Workspace folder not configured yet.")
        return Path(root) / cls.FILENAME
