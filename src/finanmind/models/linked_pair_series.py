"""Trailing-month series for one budget label ↔ credit-card category link."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LinkedPairSeries:
    """Expected budget plus monthly actuals charged to the linked CC category."""

    pair_id: str
    label_path: str
    card_category_path: str
    color: str
    expected_cop: float
    points: list[tuple[str, float]]
