"""Produces the month-vs-budget summary rows for the Distribución right panel."""

from __future__ import annotations

from finanmind.models.budget_category import BudgetCategory
from finanmind.models.budget_workspace import BudgetWorkspace
from finanmind.services.monthly_distribution_service import MonthlyDistributionService


class DistributionSummaryBuilder:
    """Pairs every budget label with its month spend and computes the diff tone."""

    _DIFF_TOLERANCE = 0.5

    @classmethod
    def build(
        cls,
        workspace: BudgetWorkspace,
        ledger: MonthlyDistributionService,
        month_key: str,
    ) -> list[dict]:
        """Return one row per label with budget, spent, diff and tone classifier."""
        spent_map = ledger.monthly_spent_by_label(month_key)
        rows: list[dict] = []
        for title, label_id, budget_amt, color in cls._flatten(workspace):
            spent = float(spent_map.get(label_id, 0.0))
            rows.append(cls._row(title, label_id, color, budget_amt, spent))
        return rows

    @classmethod
    def _row(
        cls,
        title: str,
        label_id: str,
        color: str,
        budget_amt: float,
        spent: float,
    ) -> dict:
        diff = budget_amt - spent
        return {
            "label_id": label_id,
            "title": title,
            "color": color,
            "budget_cop": budget_amt,
            "spent_cop": spent,
            "diff_cop": diff,
            "tone": cls._tone(spent, budget_amt),
        }

    @classmethod
    def _tone(cls, spent: float, budget_amt: float) -> str:
        eps = cls._DIFF_TOLERANCE
        if spent <= eps:
            return "neutral"
        if spent > budget_amt + eps:
            return "over"
        if abs(spent - budget_amt) <= eps:
            return "hit"
        return "under"

    @classmethod
    def _flatten(cls, workspace: BudgetWorkspace) -> list[tuple[str, str, float, str]]:
        rows: list[tuple[str, str, float, str]] = []
        for cat in workspace.categories:
            tint = cls._category_color(cat)
            for lbl in cat.labels:
                title = lbl.title.strip() or "Etiqueta"
                rows.append((title, lbl.label_id, lbl.amount_cop, tint))
        return rows

    @classmethod
    def _category_color(cls, cat: BudgetCategory) -> str:
        return cat.color_dark.strip() or cat.color_light.strip()
