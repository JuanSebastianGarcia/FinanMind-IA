"""Read-only bundle produced for one dashboard month."""

from __future__ import annotations

from dataclasses import dataclass

from finanmind.models.linked_pair_series import LinkedPairSeries


@dataclass(frozen=True)
class FinancialDashboardSnapshot:
    """Aggregated metrics, chart rows, and copy for the financial dashboard."""

    month_key: str
    month_label: str
    income_cop: float
    distribution_spent_cop: float
    cash_remainder_cop: float
    card_spent_month_cop: float
    card_debt_total_cop: float
    card_limit_total_cop: float
    investment_cop: float
    investment_usd: float
    investment_month_cop: float
    investment_month_usd: float
    investment_rows_cop: list[tuple[str, float, float]]
    investment_rows_usd: list[tuple[str, float, float]]
    savings_hint_cop: float
    budget_distribution_rows: list[tuple[str, float, float]]
    credit_category_rows: list[tuple[str, float, float]]
    flow_points: list[tuple[str, float, float]]
    linked_pair_series: list[LinkedPairSeries]
    insights: list[str]
    health_rows: list[tuple[str, str]]
    month_picker_keys: list[str]
