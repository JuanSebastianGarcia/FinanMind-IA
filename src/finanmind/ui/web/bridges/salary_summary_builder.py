"""Builds the salary overview block consumed by the budget panel header."""

from __future__ import annotations

from finanmind.budget.salary_shares import BudgetSalaryShares
from finanmind.models.budget_workspace import BudgetWorkspace


class SalarySummaryBuilder:
    """Produces salary metrics (allocated, available, used %, free %) as JSON."""

    @classmethod
    def build(cls, workspace: BudgetWorkspace) -> dict:
        """Return a serialisable dict describing the salary baseline state."""
        salary = workspace.salary_cop
        pairs = cls._pairs(workspace.categories)
        allocated = BudgetSalaryShares.total_allocated_cop(pairs)
        available = BudgetSalaryShares.remaining_cop(salary, pairs)
        used_pct = BudgetSalaryShares.amount_share_percent(salary, allocated)
        free_pct = BudgetSalaryShares.amount_share_percent(salary, available)
        return cls._compose(salary, allocated, available, used_pct, free_pct)

    @classmethod
    def _pairs(cls, categories) -> list[tuple[str, list[float]]]:
        return [(c.category_id, [lbl.amount_cop for lbl in c.labels]) for c in categories]

    @classmethod
    def _compose(
        cls,
        salary: float,
        allocated: float,
        available: float,
        used_pct: float,
        free_pct: float,
    ) -> dict:
        return {
            "salary_cop": salary,
            "allocated_cop": allocated,
            "available_cop": available,
            "used_percent": used_pct,
            "free_percent": free_pct,
            "over_budget": allocated > salary > 0,
        }
