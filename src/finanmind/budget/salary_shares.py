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
    def amount_share_percent(cls, salary: float, amount_cop: float) -> float:
        """Percent of salary represented by a single COP amount."""
        return (amount_cop / salary * 100.0) if salary > 0 else 0.0

    @classmethod
    def total_allocated_cop(cls, pairs: list[tuple[str, list[float]]]) -> float:
        """Sum of all label amounts across categories."""
        return sum(sum(amounts) for _, amounts in pairs)

    @classmethod
    def remaining_cop(cls, salary: float, pairs: list[tuple[str, list[float]]]) -> float:
        """Salary minus budgeted label totals (may be negative if over-allocated)."""
        return salary - cls.total_allocated_cop(pairs)

    @classmethod
    def _group_percent(cls, amounts: list[float], salary: float) -> float:
        return cls.amount_share_percent(salary, sum(amounts))
