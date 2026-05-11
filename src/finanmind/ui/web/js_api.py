"""Single object passed to PyWebview's ``js_api``; flat surface usable from JS."""

from __future__ import annotations

from finanmind.ui.web.bridges.budget_bridge import BudgetBridge
from finanmind.ui.web.bridges.distribution_bridge import DistributionBridge


class JsApi:
    """Public methods become ``window.pywebview.api.<name>`` in the browser."""

    def __init__(
        self,
        budget_bridge: BudgetBridge,
        distribution_bridge: DistributionBridge,
    ) -> None:
        self._budget = budget_bridge
        self._distribution = distribution_bridge

    def get_budget_state(self) -> dict:
        """Return the full Budget workspace snapshot for the UI to render."""
        return self._budget.get_state()

    def set_salary(self, amount: float) -> dict:
        """Update the salary baseline and return the refreshed state."""
        return self._budget.set_salary(amount)

    def add_category(self, title: str, color: str) -> dict:
        """Create a new budget category and return the refreshed state."""
        return self._budget.add_category(title, color)

    def update_category(self, category_id: str, title: str, color: str) -> dict:
        """Edit an existing budget category and return the refreshed state."""
        return self._budget.update_category(category_id, title, color)

    def delete_category(self, category_id: str) -> dict:
        """Remove a budget category and all its labels."""
        return self._budget.delete_category(category_id)

    def add_label(
        self,
        category_id: str,
        title: str,
        amount: float,
        link_id: str = "",
    ) -> dict:
        """Append a label inside a category and apply the credit-card link."""
        return self._budget.add_label(category_id, title, amount, link_id)

    def update_label(
        self,
        category_id: str,
        label_id: str,
        title: str,
        amount: float,
        link_id: str = "",
    ) -> dict:
        """Edit one label and reapply the credit-card link."""
        return self._budget.update_label(category_id, label_id, title, amount, link_id)

    def delete_label(self, category_id: str, label_id: str) -> dict:
        """Remove one label under a category."""
        return self._budget.delete_label(category_id, label_id)

    def next_palette_color(self) -> str:
        """Suggest the next preset colour for the add-category dialog."""
        return self._budget.next_palette_color()

    def get_palette_presets(self) -> list[str]:
        """Return every preset colour tile shown in the category dialog."""
        return self._budget.palette_presets()

    def get_cc_link_options(self) -> list[dict]:
        """Return the credit-card link choices used by the label dialog."""
        return self._budget.cc_link_options()

    def get_distribution_state(
        self,
        preferred_month: str = "",
        preferred_receipt_id: str = "",
    ) -> dict:
        """Return the Distribución panel snapshot honoring the JS selection hints."""
        return self._distribution.get_state(preferred_month, preferred_receipt_id or None)

    def get_distribution_label_options(self) -> list[dict]:
        """Return ``Category · Label`` options for the distribution line dialog."""
        return self._distribution.label_options()

    def add_distribution_receipt(
        self,
        occurred_on: str,
        amount: float,
        memo: str = "",
    ) -> dict:
        """Create a new income receipt and return its id plus its month."""
        return self._distribution.add_receipt(occurred_on, amount, memo)

    def delete_distribution_receipt(self, receipt_id: str) -> None:
        """Delete one income receipt and every allocation tied to it."""
        self._distribution.delete_receipt(receipt_id)

    def add_distribution_line(
        self,
        receipt_id: str,
        label_id: str,
        occurred_on: str,
        amount: float,
        memo: str = "",
    ) -> None:
        """Append an allocation under one receipt."""
        self._distribution.add_line(receipt_id, label_id, occurred_on, amount, memo)

    def delete_distribution_line(self, line_id: str) -> None:
        """Remove one allocation row."""
        self._distribution.delete_line(line_id)
