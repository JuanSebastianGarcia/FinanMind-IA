"""Single recommendation row: category, current vs suggested, delta, reason."""

from __future__ import annotations

import customtkinter as ctk

from finanmind.models.budget_review_recommendation import BudgetReviewRecommendation
from finanmind.ui.budget_ui_theme import BudgetUiTheme
from finanmind.ui.currency_presenter import CurrencyPresenter


class BudgetReviewRecommendationRow:
    """Renders one recommendation as a card with comparison and reason text."""

    def __init__(self, host: ctk.CTkFrame, rec: BudgetReviewRecommendation) -> None:
        self._host = host
        self._rec = rec

    def attach(self) -> None:
        """Mount the row inside the host; assumes host is a vertical stack."""
        card = self._make_card()
        self._mount_heading(card)
        self._mount_amounts(card)
        self._mount_reason(card)

    def _make_card(self) -> ctk.CTkFrame:
        card = ctk.CTkFrame(
            self._host,
            fg_color=BudgetUiTheme.BG_MAIN,
            corner_radius=10,
            border_width=1,
            border_color=BudgetUiTheme.BORDER,
        )
        card.pack(fill="x", padx=8, pady=4)
        return card

    def _mount_heading(self, card: ctk.CTkFrame) -> None:
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=(10, 4))
        title = f"{self._rec.category_title} · {self._rec.label_title}"
        ctk.CTkLabel(
            row,
            text=title,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=BudgetUiTheme.TXT_PRI,
            anchor="w",
        ).pack(side="left", fill="x", expand=True)
        self._mount_delta_badge(row)

    def _mount_delta_badge(self, row: ctk.CTkFrame) -> None:
        delta = self._rec.delta_cop
        sign = "+" if delta > 0 else ""
        text = f"{sign}{CurrencyPresenter.format_cop(delta)}"
        bg, fg = self._delta_palette(delta)
        ctk.CTkLabel(
            row,
            text=text,
            corner_radius=10,
            padx=10,
            pady=2,
            fg_color=bg,
            text_color=fg,
            font=ctk.CTkFont(size=11, weight="bold"),
        ).pack(side="right")

    def _delta_palette(self, delta: float) -> tuple[str, str]:
        if delta < -0.5:
            return BudgetUiTheme.BADGE_OK_BG, BudgetUiTheme.BADGE_OK_FG
        if delta > 0.5:
            return BudgetUiTheme.BADGE_WARN_BG, BudgetUiTheme.BADGE_WARN_FG
        return BudgetUiTheme.BG_HOVER, BudgetUiTheme.TXT_SEC

    def _mount_amounts(self, card: ctk.CTkFrame) -> None:
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=(0, 4))
        self._mount_amount_pair(row, "Actual", self._rec.current_amount_cop, BudgetUiTheme.TXT_SEC)
        self._mount_amount_pair(row, "Sugerido", self._rec.suggested_amount_cop, BudgetUiTheme.TXT_PRI)

    def _mount_amount_pair(self, row: ctk.CTkFrame, caption: str, amount: float, value_color: str) -> None:
        block = ctk.CTkFrame(row, fg_color="transparent")
        block.pack(side="left", padx=(0, 24))
        ctk.CTkLabel(
            block,
            text=caption,
            font=ctk.CTkFont(size=10),
            text_color=BudgetUiTheme.TXT_TER,
        ).pack(anchor="w")
        ctk.CTkLabel(
            block,
            text=CurrencyPresenter.format_cop(amount),
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=value_color,
        ).pack(anchor="w")

    def _mount_reason(self, card: ctk.CTkFrame) -> None:
        text = self._rec.reason.strip() or "Sin justificación adicional."
        ctk.CTkLabel(
            card,
            text=text,
            font=ctk.CTkFont(size=12),
            text_color=BudgetUiTheme.TXT_SEC,
            wraplength=720,
            justify="left",
            anchor="w",
        ).pack(anchor="w", padx=12, pady=(0, 12))
