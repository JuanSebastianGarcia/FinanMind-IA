"""High-contrast color palette for the budget-vs-card chart and KPIs."""

from __future__ import annotations

from typing import ClassVar


class DashboardLinkedBudgetPalette:
    """Vivid line/badge tones independent from user-picked pastels."""

    PRESETS: ClassVar[tuple[str, ...]] = (
        "#1d4ed8",
        "#dc2626",
        "#059669",
        "#d97706",
        "#7c3aed",
        "#0891b2",
        "#be185d",
        "#65a30d",
    )

    @classmethod
    def color_for(cls, index: int) -> str:
        """Pick a palette tone by series index, wrapping around."""
        if index < 0:
            index = 0
        return cls.PRESETS[index % len(cls.PRESETS)]
