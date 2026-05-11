"""Serialises the budget↔credit-card linked pair series for the chart and KPIs."""

from __future__ import annotations

from finanmind.models.linked_pair_series import LinkedPairSeries
from finanmind.services.month_label_formatter import MonthLabelFormatter
from finanmind.ui.dashboard_linked_budget_palette import DashboardLinkedBudgetPalette


class DashboardLinkedSeriesBuilder:
    """Serialises every series adding a palette colour for the lines and tiles."""

    @classmethod
    def build(cls, series: list[LinkedPairSeries]) -> list[dict]:
        """Return one dict per linked pair preserving the snapshot ordering."""
        return [cls._series_to_dict(index, item) for index, item in enumerate(series or [])]

    @classmethod
    def _series_to_dict(cls, index: int, item: LinkedPairSeries) -> dict:
        return {
            "pair_id": item.pair_id,
            "label_path": item.label_path,
            "card_category_path": item.card_category_path,
            "color": DashboardLinkedBudgetPalette.color_for(index),
            "expected_cop": item.expected_cop,
            "points": cls._serialize_points(item.points),
        }

    @classmethod
    def _serialize_points(cls, points: list[tuple[str, float]]) -> list[dict]:
        return [cls._point_to_dict(point) for point in points or []]

    @classmethod
    def _point_to_dict(cls, point: tuple[str, float]) -> dict:
        month_key, value = point
        return {
            "month_key": month_key,
            "month_label": MonthLabelFormatter.spanish_month_year(month_key),
            "value_cop": value,
        }
