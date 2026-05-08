"""Form card where the user types financial context for the AI review."""

from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from finanmind.ui.budget_ui_theme import BudgetUiTheme


class BudgetReviewFormCard:
    """Lightweight wrapper around a labeled text area plus the submit button."""

    HINT_TEXT = (
        "Cuéntale al modelo en qué está trabajando: tus metas, tus deudas, "
        "tus dificultades o lo que quieras priorizar."
    )
    EXAMPLES = (
        "Ejemplos:  «quiero ahorrar para viajar»   ·   «gasto mucho en comida»   ·   "
        "«quiero reducir mis deudas»"
    )

    def __init__(self, host: ctk.CTkFrame, on_submit: Callable[[str], None]) -> None:
        self._host = host
        self._on_submit = on_submit
        self._textbox: ctk.CTkTextbox | None = None
        self._submit_btn: ctk.CTkButton | None = None

    def attach(self) -> ctk.CTkFrame:
        """Build the card and return its root frame so callers can manage layout."""
        card = self._make_card()
        self._mount_heading(card)
        self._mount_textbox(card)
        self._mount_examples(card)
        self._mount_actions(card)
        return card

    def set_busy(self, busy: bool) -> None:
        """Disable inputs while a request is in flight."""
        state = "disabled" if busy else "normal"
        if self._textbox is not None:
            self._textbox.configure(state=state)
        if self._submit_btn is not None:
            label = "Generando..." if busy else "Generar revisión"
            self._submit_btn.configure(state=state, text=label)

    def get_context(self) -> str:
        """Return the current textarea content, trimmed."""
        if self._textbox is None:
            return ""
        return self._textbox.get("1.0", "end").strip()

    def _make_card(self) -> ctk.CTkFrame:
        card = ctk.CTkFrame(
            self._host,
            fg_color=BudgetUiTheme.BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=BudgetUiTheme.BORDER,
        )
        card.pack(fill="x", pady=(2, 10))
        return card

    def _mount_heading(self, card: ctk.CTkFrame) -> None:
        head = ctk.CTkFrame(card, fg_color="transparent")
        head.pack(fill="x", padx=18, pady=(14, 0))
        ctk.CTkLabel(
            head,
            text="Tu contexto financiero",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=BudgetUiTheme.TXT_PRI,
        ).pack(anchor="w")
        ctk.CTkLabel(
            head,
            text=self.HINT_TEXT,
            font=ctk.CTkFont(size=12),
            text_color=BudgetUiTheme.TXT_SEC,
            wraplength=820,
            justify="left",
        ).pack(anchor="w", pady=(2, 8))

    def _mount_textbox(self, card: ctk.CTkFrame) -> None:
        textbox = ctk.CTkTextbox(
            card,
            height=110,
            fg_color=BudgetUiTheme.BG_MAIN,
            border_width=1,
            border_color=BudgetUiTheme.BORDER,
            text_color=BudgetUiTheme.TXT_PRI,
            font=ctk.CTkFont(size=13),
        )
        textbox.pack(fill="x", padx=18)
        self._textbox = textbox

    def _mount_examples(self, card: ctk.CTkFrame) -> None:
        ctk.CTkLabel(
            card,
            text=self.EXAMPLES,
            font=ctk.CTkFont(size=11),
            text_color=BudgetUiTheme.TXT_TER,
            anchor="w",
            wraplength=820,
            justify="left",
        ).pack(anchor="w", padx=18, pady=(8, 0))

    def _mount_actions(self, card: ctk.CTkFrame) -> None:
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=18, pady=14)
        self._submit_btn = ctk.CTkButton(
            row,
            text="Generar revisión",
            command=self._handle_submit,
            fg_color=BudgetUiTheme.ACCENT,
            hover_color=BudgetUiTheme.ACCENT_HOVER,
            text_color="#ffffff",
            corner_radius=8,
            height=34,
            width=170,
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self._submit_btn.pack(side="right")

    def _handle_submit(self) -> None:
        self._on_submit(self.get_context())
