"""Result panel rendering the AI investment review (summary + sections)."""

from __future__ import annotations

import customtkinter as ctk

from finanmind.models.investment_review_note import InvestmentReviewNote
from finanmind.models.investment_review_result import InvestmentReviewResult
from finanmind.models.investment_review_risk import InvestmentReviewRiskLevel
from finanmind.ui.budget_ui_theme import BudgetUiTheme
from finanmind.ui.investment_review_note_row import InvestmentReviewNoteRow


class InvestmentReviewResultsPanel:
    """Owns the visual representation of one InvestmentReviewResult."""

    _WRAP_WIDTH = 640

    def __init__(self, host: ctk.CTkBaseClass) -> None:
        self._host = host
        self._frame: ctk.CTkFrame | None = None

    def render(self, result: InvestmentReviewResult) -> None:
        """Replace any previous render with a fresh result view."""
        self.clear()
        self._frame = ctk.CTkFrame(self._host, fg_color="transparent")
        self._frame.pack(fill="both", expand=True, pady=(2, 0))
        self._mount_summary_card(result)
        self._mount_research_section(result)
        self._mount_all_note_sections(result)

    def clear(self) -> None:
        """Remove the current rendering, if any."""
        if self._frame is not None:
            self._frame.destroy()
            self._frame = None

    def _mount_summary_card(self, result: InvestmentReviewResult) -> None:
        card = self._make_card_shell()
        self._mount_summary_text(card, result)
        self._mount_risk_badge(card, result.risk_level)

    def _make_card_shell(self) -> ctk.CTkFrame:
        assert self._frame is not None
        card = ctk.CTkFrame(
            self._frame,
            fg_color=BudgetUiTheme.BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=BudgetUiTheme.BORDER,
        )
        card.pack(fill="x", pady=(0, 10))
        return card

    def _mount_summary_text(self, card: ctk.CTkFrame, result: InvestmentReviewResult) -> None:
        ctk.CTkLabel(
            card,
            text="Resumen del análisis",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=BudgetUiTheme.TXT_PRI,
        ).pack(anchor="w", padx=18, pady=(14, 4))
        body = result.summary.strip() or "El modelo no devolvió un resumen."
        ctk.CTkLabel(
            card,
            text=body,
            font=ctk.CTkFont(size=12),
            text_color=BudgetUiTheme.TXT_SEC,
            wraplength=self._WRAP_WIDTH,
            justify="left",
            anchor="w",
        ).pack(anchor="w", padx=18, pady=(0, 8), fill="x")

    def _mount_risk_badge(self, card: ctk.CTkFrame, risk: InvestmentReviewRiskLevel) -> None:
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=18, pady=(0, 14))
        ctk.CTkLabel(
            row,
            text="Nivel de riesgo:",
            font=ctk.CTkFont(size=11),
            text_color=BudgetUiTheme.TXT_TER,
        ).pack(side="left", padx=(0, 8))
        bg, fg, label = self._risk_palette(risk)
        ctk.CTkLabel(
            row,
            text=label,
            corner_radius=10,
            padx=10,
            pady=2,
            fg_color=bg,
            text_color=fg,
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(side="left")

    def _risk_palette(self, risk: InvestmentReviewRiskLevel) -> tuple[str, str, str]:
        if risk == InvestmentReviewRiskLevel.HIGH:
            return BudgetUiTheme.BADGE_WARN_BG, BudgetUiTheme.BADGE_WARN_FG, "Alto"
        if risk == InvestmentReviewRiskLevel.LOW:
            return BudgetUiTheme.BADGE_OK_BG, BudgetUiTheme.BADGE_OK_FG, "Bajo"
        return BudgetUiTheme.INFO_BG, BudgetUiTheme.ACCENT, "Medio"

    def _mount_all_note_sections(self, result: InvestmentReviewResult) -> None:
        self._mount_note_section("Decisiones que tomaría", result.decisions)
        self._mount_note_section("En qué invertiría", result.ideas)
        self._mount_note_section("Cambios al portafolio actual", result.portfolio_changes)

    def _mount_note_section(self, heading: str, notes: list[InvestmentReviewNote]) -> None:
        assert self._frame is not None
        self._section_heading(heading)
        host = self._make_list_host()
        if not notes:
            self._render_empty_note(host)
            return
        for note in notes:
            InvestmentReviewNoteRow(host, note).attach()

    def _section_heading(self, text: str) -> None:
        assert self._frame is not None
        ctk.CTkLabel(
            self._frame,
            text=text,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=BudgetUiTheme.TXT_PRI,
        ).pack(anchor="w", pady=(8, 4))

    def _make_list_host(self) -> ctk.CTkFrame:
        assert self._frame is not None
        host = ctk.CTkFrame(
            self._frame,
            fg_color=BudgetUiTheme.BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=BudgetUiTheme.BORDER,
        )
        host.pack(fill="x", pady=(0, 4))
        return host

    def _render_empty_note(self, host: ctk.CTkFrame) -> None:
        ctk.CTkLabel(
            host,
            text="La IA no propuso elementos en esta sección.",
            font=ctk.CTkFont(size=12),
            text_color=BudgetUiTheme.TXT_SEC,
            wraplength=self._WRAP_WIDTH,
            justify="left",
        ).pack(anchor="w", padx=14, pady=14)

    def _mount_research_section(self, result: InvestmentReviewResult) -> None:
        if not result.research_notes:
            return
        self._section_heading("Investigación previa")
        host = self._make_list_host()
        for raw in result.research_notes:
            self._render_research_bullet(host, raw)

    def _render_research_bullet(self, host: ctk.CTkFrame, text: str) -> None:
        clean = text.strip()
        if clean == "":
            return
        ctk.CTkLabel(
            host,
            text=f"• {clean}",
            font=ctk.CTkFont(size=12),
            text_color=BudgetUiTheme.TXT_SEC,
            wraplength=self._WRAP_WIDTH,
            justify="left",
            anchor="w",
        ).pack(anchor="w", padx=14, pady=(6, 6), fill="x")
