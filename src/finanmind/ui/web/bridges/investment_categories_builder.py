"""Serialises investment categories (id + name) for the manager dialog and pickers."""

from __future__ import annotations

from finanmind.models.investment_category import InvestmentCategory


class InvestmentCategoriesBuilder:
    """Produces the categories list payload sorted alphabetically (case-insensitive)."""

    @classmethod
    def build(cls, categories: list[InvestmentCategory]) -> list[dict]:
        """Return one dict per category, ready for JSON transport."""
        ordered = sorted(categories, key=lambda c: c.name.lower())
        return [{"category_id": cat.category_id, "name": cat.name} for cat in ordered]
