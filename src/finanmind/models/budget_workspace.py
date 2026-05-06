"""Full persisted budget snapshot."""

from __future__ import annotations

from dataclasses import dataclass, field

from finanmind.models.budget_category import BudgetCategory


@dataclass
class BudgetWorkspace:
    """Monthly salary baseline plus ordered budget categories."""

    salary_cop: float
    categories: list[BudgetCategory] = field(default_factory=list)
