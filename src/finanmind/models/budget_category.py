"""Budget category grouping labels."""

from __future__ import annotations

from dataclasses import dataclass, field

from finanmind.models.budget_label import BudgetLabel


@dataclass
class BudgetCategory:
    """Category owns presentation colors and zero or more labels."""

    category_id: str
    title: str
    color_light: str
    color_dark: str
    labels: list[BudgetLabel] = field(default_factory=list)
