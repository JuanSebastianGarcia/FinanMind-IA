"""Single object passed to PyWebview's ``js_api``; flat surface usable from JS."""

from __future__ import annotations

from finanmind.ui.web.bridges.budget_bridge import BudgetBridge
from finanmind.ui.web.bridges.budget_review_bridge import BudgetReviewBridge
from finanmind.ui.web.bridges.cards_bridge import CardsBridge
from finanmind.ui.web.bridges.dashboard_bridge import DashboardBridge
from finanmind.ui.web.bridges.distribution_bridge import DistributionBridge
from finanmind.ui.web.bridges.investment_bridge import InvestmentBridge
from finanmind.ui.web.bridges.investment_review_bridge import InvestmentReviewBridge


class JsApi:
    """Public methods become ``window.pywebview.api.<name>`` in the browser."""

    def __init__(
        self,
        budget_bridge: BudgetBridge,
        distribution_bridge: DistributionBridge,
        cards_bridge: CardsBridge,
        investment_bridge: InvestmentBridge,
        investment_review_bridge: InvestmentReviewBridge,
        dashboard_bridge: DashboardBridge,
        budget_review_bridge: BudgetReviewBridge,
    ) -> None:
        self._budget = budget_bridge
        self._distribution = distribution_bridge
        self._cards = cards_bridge
        self._investments = investment_bridge
        self._review = investment_review_bridge
        self._dashboard = dashboard_bridge
        self._budget_review = budget_review_bridge

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

    def get_cards_dashboard_state(self) -> dict:
        """Return the snapshot used by the credit-cards dashboard grid."""
        return self._cards.dashboard_state()

    def get_card_detail_state(self, card_id: str, preferred_cycle: str = "") -> dict:
        """Return the snapshot used by a single credit-card detail view."""
        return self._cards.detail_state(card_id, preferred_cycle)

    def get_cards_label_options(self) -> list[dict]:
        """Return the budget-label options used by the card-category dialog."""
        return self._cards.label_options()

    def get_cards_palette_presets(self) -> list[str]:
        """Return the preset colours shared with the budget palette."""
        return self._cards.palette_presets()

    def add_card(
        self,
        name: str,
        limit: float,
        cut_day: int,
        payment_due_day: int,
        color: str = "",
    ) -> dict:
        """Persist a new credit card and return its id."""
        return self._cards.add_card(name, limit, cut_day, payment_due_day, color)

    def update_card(
        self,
        card_id: str,
        name: str,
        limit: float,
        cut_day: int,
        payment_due_day: int,
        color: str = "",
    ) -> None:
        """Edit one credit card in place."""
        self._cards.update_card(card_id, name, limit, cut_day, payment_due_day, color)

    def delete_card(self, card_id: str) -> None:
        """Remove a card with all its categories, expenses and payments."""
        self._cards.delete_card(card_id)

    def add_card_category(
        self,
        card_id: str,
        title: str,
        color: str = "",
        link_id: str = "",
    ) -> None:
        """Append a new expense category bound to a card."""
        self._cards.add_category(card_id, title, color, link_id)

    def update_card_category(
        self,
        category_id: str,
        title: str,
        color: str = "",
        link_id: str = "",
    ) -> None:
        """Edit one card category and (re)apply its budget-label link."""
        self._cards.update_category(category_id, title, color, link_id)

    def delete_card_category(self, category_id: str) -> None:
        """Remove one card category, clearing it from existing expenses."""
        self._cards.delete_category(category_id)

    def add_card_expense(
        self,
        card_id: str,
        category_id: str,
        occurred_on: str,
        total_amount_cop: float,
        description: str,
        installments: int = 1,
        notes: str = "",
    ) -> None:
        """Append a new charge under a card. For installments > 1 sibling records are created."""
        self._cards.add_expense(
            card_id, category_id, occurred_on, total_amount_cop, description, installments, notes,
        )

    def update_card_expense(
        self,
        expense_id: str,
        category_id: str,
        occurred_on: str,
        total_amount_cop: float,
        description: str,
        notes: str = "",
    ) -> None:
        """Edit an existing charge in place."""
        self._cards.update_expense(
            expense_id, category_id, occurred_on, total_amount_cop, description, notes,
        )

    def delete_card_expense(self, expense_id: str) -> None:
        """Remove one charge."""
        self._cards.delete_expense(expense_id)

    def add_card_payment(
        self,
        card_id: str,
        paid_on: str,
        amount: float,
        notes: str = "",
    ) -> None:
        """Register a payment for one card."""
        self._cards.add_payment(card_id, paid_on, amount, notes)

    def delete_card_payment(self, payment_id: str) -> None:
        """Remove one payment from the card history."""
        self._cards.delete_payment(payment_id)

    def get_investments_state(self) -> dict:
        """Return the full Investments panel snapshot (summary, entries, charts)."""
        return self._investments.get_state()

    def add_investment_category(self, name: str) -> dict:
        """Persist a new investment category and return the refreshed state."""
        return self._investments.add_category(name)

    def update_investment_category(self, category_id: str, name: str) -> dict:
        """Rename one investment category and return the refreshed state."""
        return self._investments.update_category(category_id, name)

    def delete_investment_category(self, category_id: str) -> dict:
        """Drop one investment category and return the refreshed state."""
        return self._investments.delete_category(category_id)

    def add_investment_entry(
        self,
        category_id: str,
        amount: float,
        invested_date_iso: str,
        description: str,
        currency_code: str,
    ) -> dict:
        """Register a new holding and return the refreshed state."""
        return self._investments.add_entry(
            category_id, amount, invested_date_iso, description, currency_code,
        )

    def update_investment_entry(
        self,
        investment_id: str,
        category_id: str,
        amount: float,
        invested_date_iso: str,
        description: str,
        currency_code: str,
    ) -> dict:
        """Edit an existing holding and return the refreshed state."""
        return self._investments.update_entry(
            investment_id, category_id, amount, invested_date_iso, description, currency_code,
        )

    def delete_investment_entry(self, investment_id: str) -> dict:
        """Remove one holding and return the refreshed state."""
        return self._investments.delete_entry(investment_id)

    def get_investment_review_setup(self) -> dict:
        """Return rules, exchange rate, AI status, and credentials readiness."""
        return self._review.get_setup()

    def add_investment_review_rule(self, text: str) -> list[dict]:
        """Append a new personal rule and return the refreshed rules list."""
        return self._review.add_rule(text)

    def update_investment_review_rule(self, rule_id: str, text: str) -> list[dict]:
        """Edit an existing personal rule and return the refreshed rules list."""
        return self._review.update_rule(rule_id, text)

    def delete_investment_review_rule(self, rule_id: str) -> list[dict]:
        """Remove one personal rule and return the refreshed rules list."""
        return self._review.delete_rule(rule_id)

    def run_investment_review(self, rate: float) -> dict:
        """Submit the portfolio to the AI and return the review payload."""
        return self._review.analyze(rate)

    def get_dashboard_state(self, preferred_month: str = "") -> dict:
        """Return the cross-domain dashboard snapshot for ``yyyy-mm``."""
        return self._dashboard.get_state(preferred_month)

    def get_budget_review_setup(self) -> dict:
        """Return AI vendor + model and credentials readiness for the review dialog."""
        return self._budget_review.get_setup()

    def set_budget_review_provider(self, vendor: str) -> dict:
        """Persist the quick provider choice and return the refreshed setup."""
        return self._budget_review.set_provider(vendor)

    def run_budget_review(self, context: str) -> dict:
        """Submit the workspace plus free-form context and return the AI payload."""
        return self._budget_review.run_review(context)

    def apply_budget_review_recommendations(self, recommendations: list[dict]) -> dict:
        """Apply accepted recommendations and return ``{changed, state}`` with the new workspace."""
        changed = self._budget_review.apply_recommendations(recommendations)
        return {"changed": changed, "state": self._budget.get_state()}

    def get_budget_review_llm_settings(self) -> dict:
        """Return the per-vendor API key, model and env locks for the settings dialog."""
        return self._budget_review.get_llm_settings()

    def save_budget_review_llm_settings(
        self,
        provider: str,
        api_key: str,
        model_id: str,
    ) -> dict:
        """Persist provider + credentials and return the refreshed review setup."""
        return self._budget_review.save_llm_settings(provider, api_key, model_id)
