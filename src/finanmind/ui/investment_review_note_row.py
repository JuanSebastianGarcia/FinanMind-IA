"""Single note row rendered inside an investment review section."""

from __future__ import annotations

import customtkinter as ctk

from finanmind.models.investment_review_note import InvestmentReviewNote
from finanmind.ui.budget_ui_theme import BudgetUiTheme


class InvestmentReviewNoteRow:
    """Renders one bullet (title + detail) as a card inside a vertical stack."""

    _WRAP_WIDTH = 620

    def __init__(self, host: ctk.CTkBaseClass, note: InvestmentReviewNote) -> None:
        self._host = host
        self._note = note

    def attach(self) -> None:
        """Mount the row inside the host."""
        card = self._make_card()
        self._mount_title(card)
        self._mount_detail(card)

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

    def _mount_title(self, card: ctk.CTkFrame) -> None:
        title = self._note.cleaned_title() or "(sin título)"
        ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=BudgetUiTheme.TXT_PRI,
            anchor="w",
            justify="left",
            wraplength=self._WRAP_WIDTH,
        ).pack(anchor="w", padx=12, pady=(10, 2), fill="x")

    def _mount_detail(self, card: ctk.CTkFrame) -> None:
        detail = self._note.cleaned_detail() or "Sin detalle adicional."
        ctk.CTkLabel(
            card,
            text=detail,
            font=ctk.CTkFont(size=12),
            text_color=BudgetUiTheme.TXT_SEC,
            wraplength=self._WRAP_WIDTH,
            justify="left",
            anchor="w",
        ).pack(anchor="w", padx=12, pady=(0, 12), fill="x")
