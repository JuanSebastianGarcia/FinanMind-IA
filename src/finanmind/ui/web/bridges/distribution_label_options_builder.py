"""Produces the budget-label options consumed by the distribution line dialog."""

from __future__ import annotations

from finanmind.models.budget_category import BudgetCategory
from finanmind.models.budget_workspace import BudgetWorkspace


class DistributionLabelOptionsBuilder:
    """Flattens ``Category · Label`` pairs into a JSON-friendly list."""

    @classmethod
    def build(cls, workspace: BudgetWorkspace) -> list[dict]:
        """Return one dict per budget label with caption, label_id and accent color."""
        out: list[dict] = []
        for cat in workspace.categories:
            prefix = cls._category_prefix(cat)
            color = cls._resolve_color(cat)
            for lbl in cat.labels:
                out.append({
                    "caption": f"{prefix}{lbl.title}",
                    "label_id": lbl.label_id,
                    "color": color,
                })
        return out

    @classmethod
    def _category_prefix(cls, cat: BudgetCategory) -> str:
        title = cat.title.strip()
        return "" if title == "" else f"{title} · "

    @classmethod
    def _resolve_color(cls, cat: BudgetCategory) -> str:
        return cat.color_dark.strip() or cat.color_light.strip()
