"""Result panel rendering AI summary, recommendations, and accept/reject."""

from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from finanmind.models.budget_review_result import BudgetReviewResult
from finanmind.models.budget_review_risk import BudgetReviewRiskLevel
from finanmind.ui.budget_review_recommendation_row import BudgetReviewRecommendationRow
from finanmind.ui.budget_ui_theme import BudgetUiTheme
from finanmind.ui.currency_presenter import CurrencyPresenter


class BudgetReviewResultsPanel:
    """Owns the visual representation of one BudgetReviewResult."""

    def __init__(
        self,
        host: ctk.CTkFrame,
        on_accept: Callable[[], None],
        on_reject: Callable[[], None],
    ) -> None:
        self._host = host
        self._on_accept = on_accept
        self._on_reject = on_reject
        self._frame: ctk.CTkFrame | None = None

    def render(self, result: BudgetReviewResult) -> None:
        """Replace any previous render with a fresh result view."""
        self.clear()
        self._frame = ctk.CTkFrame(self._host, fg_color="transparent")
        self._frame.pack(fill="x", expand=False, pady=(2, 0))
        self._mount_summary_card(result)
        self._mount_recommendations_section(result)
        self._mount_action_bar(result)

    def clear(self) -> None:
        """Remove the current rendering, if any."""
        if self._frame is not None:
            self._frame.destroy()
            self._frame = None

    def _mount_summary_card(self, result: BudgetReviewResult) -> None:
        assert self._frame is not None
        card = ctk.CTkFrame(
            self._frame,
            fg_color=BudgetUiTheme.BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=BudgetUiTheme.BORDER,
        )
        card.pack(fill="x", pady=(0, 10))
        self._mount_summary_text(card, result)
        self._mount_summary_metrics(card, result)

    def _mount_summary_text(self, card: ctk.CTkFrame, result: BudgetReviewResult) -> None:
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
            wraplength=820,
            justify="left",
            anchor="w",
        ).pack(anchor="w", padx=18, pady=(0, 12))

    def _mount_summary_metrics(self, card: ctk.CTkFrame, result: BudgetReviewResult) -> None:
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=18, pady=(0, 14))
        self._mount_metric(row, "Ahorro proyectado", CurrencyPresenter.format_cop(result.projected_savings_cop))
        self._mount_metric(row, "Cambios", str(len(result.recommendations)))
        self._mount_risk_metric(row, result.risk_level)

    def _mount_metric(self, row: ctk.CTkFrame, caption: str, value: str) -> None:
        block = ctk.CTkFrame(row, fg_color="transparent")
        block.pack(side="left", padx=(0, 28))
        ctk.CTkLabel(
            block,
            text=caption,
            font=ctk.CTkFont(size=11),
            text_color=BudgetUiTheme.TXT_TER,
        ).pack(anchor="w")
        ctk.CTkLabel(
            block,
            text=value,
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=BudgetUiTheme.TXT_PRI,
        ).pack(anchor="w")

    def _mount_risk_metric(self, row: ctk.CTkFrame, risk: BudgetReviewRiskLevel) -> None:
        block = ctk.CTkFrame(row, fg_color="transparent")
        block.pack(side="left")
        ctk.CTkLabel(
            block,
            text="Riesgo",
            font=ctk.CTkFont(size=11),
            text_color=BudgetUiTheme.TXT_TER,
        ).pack(anchor="w")
        bg, fg, label = self._risk_palette(risk)
        ctk.CTkLabel(
            block,
            text=label,
            corner_radius=10,
            padx=10,
            pady=2,
            fg_color=bg,
            text_color=fg,
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(anchor="w", pady=(2, 0))

    def _risk_palette(self, risk: BudgetReviewRiskLevel) -> tuple[str, str, str]:
        if risk == BudgetReviewRiskLevel.HIGH:
            return BudgetUiTheme.BADGE_WARN_BG, BudgetUiTheme.BADGE_WARN_FG, "Alto"
        if risk == BudgetReviewRiskLevel.LOW:
            return BudgetUiTheme.BADGE_OK_BG, BudgetUiTheme.BADGE_OK_FG, "Bajo"
        return BudgetUiTheme.INFO_BG, BudgetUiTheme.ACCENT, "Medio"

    def _mount_recommendations_section(self, result: BudgetReviewResult) -> None:
        assert self._frame is not None
        self._heading_recommendations()
        box = self._make_list_host()
        if not result.recommendations:
            self._render_empty(box)
            return
        for rec in result.recommendations:
            BudgetReviewRecommendationRow(box, rec).attach()

    def _heading_recommendations(self) -> None:
        assert self._frame is not None
        ctk.CTkLabel(
            self._frame,
            text="Recomendaciones",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=BudgetUiTheme.TXT_PRI,
        ).pack(anchor="w", pady=(2, 4))

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

    def _render_empty(self, host: ctk.CTkFrame) -> None:
        ctk.CTkLabel(
            host,
            text="La IA no propuso cambios. Tu presupuesto luce bien para el contexto dado.",
            font=ctk.CTkFont(size=12),
            text_color=BudgetUiTheme.TXT_SEC,
            wraplength=720,
            justify="left",
        ).pack(anchor="w", padx=14, pady=14)

    def _mount_action_bar(self, result: BudgetReviewResult) -> None:
        assert self._frame is not None
        bar = ctk.CTkFrame(self._frame, fg_color="transparent")
        bar.pack(fill="x", pady=(12, 0))
        self._mount_reject_button(bar)
        self._mount_accept_button(bar, result)

    def _mount_reject_button(self, bar: ctk.CTkFrame) -> None:
        ctk.CTkButton(
            bar,
            text="Descartar",
            command=self._on_reject,
            fg_color="transparent",
            text_color=BudgetUiTheme.TXT_SEC,
            hover_color=BudgetUiTheme.BG_HOVER,
            border_color=BudgetUiTheme.BORDER,
            border_width=1,
            corner_radius=8,
            height=34,
            width=140,
            font=ctk.CTkFont(size=12),
        ).pack(side="right", padx=(8, 0))

    def _mount_accept_button(self, bar: ctk.CTkFrame, result: BudgetReviewResult) -> None:
        enabled = result.has_changes()
        ctk.CTkButton(
            bar,
            text="Aplicar al presupuesto",
            command=self._on_accept,
            state="normal" if enabled else "disabled",
            fg_color=BudgetUiTheme.ACCENT,
            hover_color=BudgetUiTheme.ACCENT_HOVER,
            text_color="#ffffff",
            corner_radius=8,
            height=34,
            width=200,
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(side="right")
