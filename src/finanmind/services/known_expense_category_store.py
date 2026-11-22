"""Remembers which card category an expense description maps to, per card."""

from __future__ import annotations

import csv
from pathlib import Path

from finanmind.config import AppConfig
from finanmind.storage.d1_client import D1ClientProvider
from finanmind.storage.runtime_environment import RuntimeEnvironment

_FIELDNAMES = ["card_id", "description_key", "category_id"]


class KnownExpenseCategoryStore:
    """``(card_id, description) -> category_id`` lookup for NU auto-registration.

    Backed by a workspace CSV in development and by the D1 table
    ``known_expense_categories`` in production.
    """

    FILENAME = "known_expense_categories.csv"

    @classmethod
    def lookup(cls, card_id: str, description: str) -> str | None:
        """Return the remembered category id for this description on this card, if any."""
        key = cls._normalize(description)
        if RuntimeEnvironment.uses_cloud_storage():
            return _D1KnownExpenseCategories.lookup(card_id, key)
        for row in cls._read_all():
            if row["card_id"] == card_id and row["description_key"] == key:
                return row["category_id"]
        return None

    @classmethod
    def remember(cls, card_id: str, description: str, category_id: str) -> None:
        """Store (or update) the category this description should map to on this card."""
        key = cls._normalize(description)
        if RuntimeEnvironment.uses_cloud_storage():
            _D1KnownExpenseCategories.remember(card_id, key, category_id)
            return
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


class _D1KnownExpenseCategories:
    """Production backend; rows cascade away when their card or category is deleted."""

    @staticmethod
    def lookup(card_id: str, key: str) -> str | None:
        rows = D1ClientProvider.shared().query(
            "SELECT category_id FROM known_expense_categories WHERE card_id = ? AND description_key = ?",
            card_id,
            key,
        )
        return rows[0]["category_id"] if rows else None

    @staticmethod
    def remember(card_id: str, key: str, category_id: str) -> None:
        # Only a hint for future imports: if the card or category is gone, skip it
        # silently instead of failing a registration that already succeeded.
        D1ClientProvider.shared().query(
            "INSERT INTO known_expense_categories (card_id, description_key, category_id) "
            "SELECT ?, ?, ? WHERE EXISTS (SELECT 1 FROM credit_cards WHERE card_id = ?) "
            "AND EXISTS (SELECT 1 FROM credit_card_categories WHERE category_id = ?) "
            "ON CONFLICT (card_id, description_key) DO UPDATE SET category_id = excluded.category_id",
            card_id,
            key,
            category_id,
            card_id,
            category_id,
        )
