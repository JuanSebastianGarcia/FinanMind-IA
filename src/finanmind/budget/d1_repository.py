"""Budget workspace persisted in Cloudflare D1 (production backend of ``BudgetRepository``)."""

from __future__ import annotations

from finanmind.models.budget_category import BudgetCategory
from finanmind.models.budget_label import BudgetLabel
from finanmind.models.budget_workspace import BudgetWorkspace
from finanmind.storage.d1_client import D1Client
from finanmind.storage.d1_table_sync import D1Table, D1TableSync, Row


class BudgetD1Repository:
    """Same contract as ``BudgetRepository`` (``load_workspace`` / ``save_workspace``)."""

    SALARY = D1Table("budget_salary", ("id",), ("id", "amount_cop"))
    CATEGORIES = D1Table(
        "budget_categories",
        ("category_id",),
        ("category_id", "title", "color_light", "color_dark", "position"),
        order_by="position, category_id",
    )
    LABELS = D1Table(
        "budget_labels",
        ("label_id",),
        ("label_id", "category_id", "title", "amount_cop", "position"),
        order_by="position, label_id",
    )

    def __init__(self, client: D1Client) -> None:
        self._client = client
        self._salary = D1TableSync(self.SALARY)
        self._categories = D1TableSync(self.CATEGORIES)
        self._labels = D1TableSync(self.LABELS)

    def load_workspace(self) -> BudgetWorkspace:
        salary_rows, category_rows, label_rows = D1TableSync.read(
            self._client, [self._salary, self._categories, self._labels]
        )
        salary = float(salary_rows[0]["amount_cop"]) if salary_rows else 0.0
        categories = [
            BudgetCategory(
                category_id=r["category_id"],
                title=r["title"],
                color_light=r["color_light"],
                color_dark=r["color_dark"],
                labels=[],
            )
            for r in category_rows
        ]
        by_id = {c.category_id: c for c in categories}
        for r in label_rows:
            parent = by_id.get(r["category_id"])
            if parent is not None:
                parent.labels.append(
                    BudgetLabel(label_id=r["label_id"], title=r["title"], amount_cop=float(r["amount_cop"]))
                )
        return BudgetWorkspace(salary_cop=salary, categories=categories)

    def save_workspace(self, workspace: BudgetWorkspace) -> None:
        salary_rows: list[Row] = [{"id": "salary", "amount_cop": _cop(workspace.salary_cop)}]
        category_rows: list[Row] = []
        label_rows: list[Row] = []
        for cat_pos, cat in enumerate(workspace.categories):
            category_rows.append(
                {
                    "category_id": cat.category_id,
                    "title": cat.title,
                    "color_light": cat.color_light,
                    "color_dark": cat.color_dark,
                    "position": cat_pos,
                }
            )
            for label_pos, label in enumerate(cat.labels):
                label_rows.append(
                    {
                        "label_id": label.label_id,
                        "category_id": cat.category_id,
                        "title": label.title,
                        "amount_cop": _cop(label.amount_cop),
                        "position": label_pos,
                    }
                )
        D1TableSync.write(
            self._client,
            [(self._salary, salary_rows), (self._categories, category_rows), (self._labels, label_rows)],
        )


def _cop(amount: float) -> int:
    """COP amounts are stored as whole pesos, like the CSV codec does."""
    return int(round(amount))
