"""Percent of salary represented by each category's label totals."""


class BudgetSalaryShares:
    """Maps category identifiers to their share of the monthly salary baseline."""

    @classmethod
    def map_by_category(
        cls,
        salary: float,
        pairs: list[tuple[str, list[float]]],
    ) -> dict[str, float]:
        """Build ``category_id -> percent`` for supplied label amount lists."""
        return {category_id: cls._group_percent(amounts, salary) for category_id, amounts in pairs}

    @classmethod
    def _group_percent(cls, amounts: list[float], salary: float) -> float:
        total = sum(amounts)
        return (total / salary * 100.0) if salary > 0 else 0.0
