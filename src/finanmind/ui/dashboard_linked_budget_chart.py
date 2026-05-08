"""Line chart of actual CC spending vs expected budget per linked pair."""

from __future__ import annotations

import tkinter as tk

import customtkinter as ctk

from finanmind.models.linked_pair_series import LinkedPairSeries
from finanmind.services.month_label_formatter import MonthLabelFormatter
from finanmind.ui.budget_ui_theme import BudgetUiTheme
from finanmind.ui.dashboard_linked_budget_palette import DashboardLinkedBudgetPalette


class DashboardLinkedBudgetChart:
    """Draws monthly actual vs budget polylines for label↔CC links."""

    _MARGIN_LEFT = 64
    _MARGIN_RIGHT = 18
    _MARGIN_TOP = 26
    _MARGIN_BOTTOM = 30

    def __init__(self, parent: ctk.CTkFrame) -> None:
        self._parent = parent
        self._canvas: tk.Canvas | None = None
        self._series: list[LinkedPairSeries] = []
        self._focus_id = ""
        self._span = 6
        self._anchor = ""

    def attach(self) -> None:
        """Create the canvas and bind resize redraws."""
        canvas = tk.Canvas(
            self._parent,
            height=260,
            bg=BudgetUiTheme.BG_CARD,
            highlightthickness=0,
            bd=0,
        )
        canvas.pack(fill="both", expand=True, padx=10, pady=8)
        canvas.bind("<Configure>", self._on_cfg)
        self._canvas = canvas

    def set_data(
        self,
        series: list[LinkedPairSeries],
        focus_pair_id: str,
        span_months: int,
        anchor_month: str,
    ) -> None:
        """Update inputs and redraw."""
        self._series = list(series)
        self._focus_id = focus_pair_id
        self._span = max(1, span_months)
        self._anchor = anchor_month
        self._redraw()

    def _on_cfg(self, _event: object) -> None:
        self._redraw()

    def _redraw(self) -> None:
        if self._canvas is None:
            return
        self._canvas.delete("all")
        w = float(self._canvas.winfo_width())
        h = float(self._canvas.winfo_height())
        if w < 100 or h < 80:
            return
        if not self._series:
            self._draw_empty(w, h)
            return
        self._draw_chart(w, h)

    def _draw_empty(self, w: float, h: float) -> None:
        assert self._canvas is not None
        self._canvas.create_text(
            w / 2,
            h / 2,
            text="Enlaza una etiqueta del presupuesto a una categoría de tarjeta para verla aquí",
            fill=BudgetUiTheme.TXT_TER,
            font=("Segoe UI", 12),
        )

    def _draw_chart(self, w: float, h: float) -> None:
        months = self._visible_months()
        focus = self._focus_series()
        targets = [focus] if focus is not None else self._series
        peak = self._peak(targets, months)
        box = self._plot_box(w, h)
        self._draw_axes(box, peak, months)
        if focus is not None:
            self._draw_single(box, focus, months, peak)
        else:
            self._draw_multi(box, months, peak)

    def _plot_box(self, w: float, h: float) -> tuple[float, float, float, float]:
        return (
            float(self._MARGIN_LEFT),
            float(self._MARGIN_TOP),
            w - self._MARGIN_RIGHT,
            h - self._MARGIN_BOTTOM,
        )

    def _focus_series(self) -> LinkedPairSeries | None:
        if not self._focus_id:
            return None
        for s in self._series:
            if s.pair_id == self._focus_id:
                return s
        return None

    def _visible_months(self) -> list[str]:
        if not self._series:
            return []
        months = [m for m, _ in self._series[0].points]
        return months[-self._span:] if len(months) > self._span else months

    def _peak(self, targets: list[LinkedPairSeries], months: list[str]) -> float:
        peak = 1.0
        for s in targets:
            for m, v in s.points:
                if m in months:
                    peak = max(peak, v)
            peak = max(peak, s.expected_cop)
        return peak * 1.1

    def _draw_axes(self, box: tuple[float, float, float, float], peak: float, months: list[str]) -> None:
        self._draw_grid(box)
        self._draw_y_labels(box, peak)
        self._draw_x_labels(box, months)

    def _draw_grid(self, box: tuple[float, float, float, float]) -> None:
        assert self._canvas is not None
        x0, y0, x1, y1 = box
        for fr in (0.0, 0.5, 1.0):
            y = y1 - (y1 - y0) * fr
            self._canvas.create_line(x0, y, x1, y, fill=BudgetUiTheme.BORDER, width=1, dash=(2, 3))

    def _draw_x_labels(self, box: tuple[float, float, float, float], months: list[str]) -> None:
        assert self._canvas is not None
        n = len(months)
        if n <= 0:
            return
        _, _, _, y1 = box
        for i, m in enumerate(months):
            x = self._x_for(box, i, n)
            self._canvas.create_text(x, y1 + 14, text=self._short_month(m), fill=BudgetUiTheme.TXT_TER, font=("Segoe UI", 9))

    def _draw_y_labels(self, box: tuple[float, float, float, float], peak: float) -> None:
        assert self._canvas is not None
        x0, y0, _, y1 = box
        for fr in (0.0, 0.5, 1.0):
            y = y1 - (y1 - y0) * fr
            cap = self._format_short(peak * fr)
            self._canvas.create_text(x0 - 8, y, text=cap, fill=BudgetUiTheme.TXT_TER, font=("Segoe UI", 9), anchor="e")

    def _short_month(self, mk: str) -> str:
        full = MonthLabelFormatter.spanish_month_year(mk)
        head = full.split(" ", 1)[0] if " " in full else full
        return head[:3]

    def _format_short(self, val: float) -> str:
        if val >= 1_000_000:
            return f"{val / 1_000_000:.1f}M"
        if val >= 1_000:
            return f"{val / 1_000:.0f}K"
        return f"{val:.0f}"

    def _x_for(self, box: tuple[float, float, float, float], idx: int, count: int) -> float:
        x0, _, x1, _ = box
        if count <= 1:
            return (x0 + x1) / 2.0
        return x0 + (x1 - x0) * idx / (count - 1)

    def _y_for(self, box: tuple[float, float, float, float], val: float, peak: float) -> float:
        _, y0, _, y1 = box
        if peak <= 0:
            return y1
        fr = max(0.0, min(1.0, val / peak))
        return y1 - (y1 - y0) * fr

    def _draw_single(
        self,
        box: tuple[float, float, float, float],
        s: LinkedPairSeries,
        months: list[str],
        peak: float,
    ) -> None:
        color = DashboardLinkedBudgetPalette.color_for(self._index_of(s))
        pts = self._series_points(box, s, months, peak)
        self._draw_budget_line(box, s, peak, color)
        self._draw_polyline(pts, color, 4)
        self._draw_markers(pts, s, color)
        self._draw_focus_caption(box, s, color)

    def _draw_multi(self, box: tuple[float, float, float, float], months: list[str], peak: float) -> None:
        for i, s in enumerate(self._series):
            color = DashboardLinkedBudgetPalette.color_for(i)
            pts = self._series_points(box, s, months, peak)
            self._draw_polyline(pts, color, 3)
        self._draw_multi_caption(box)

    def _index_of(self, s: LinkedPairSeries) -> int:
        for i, item in enumerate(self._series):
            if item.pair_id == s.pair_id:
                return i
        return 0

    def _series_points(
        self,
        box: tuple[float, float, float, float],
        s: LinkedPairSeries,
        months: list[str],
        peak: float,
    ) -> list[tuple[float, float, float]]:
        by_month = dict(s.points)
        out: list[tuple[float, float, float]] = []
        for i, m in enumerate(months):
            v = by_month.get(m, 0.0)
            x = self._x_for(box, i, len(months))
            y = self._y_for(box, v, peak)
            out.append((x, y, v))
        return out

    def _draw_budget_line(
        self, box: tuple[float, float, float, float], s: LinkedPairSeries, peak: float, color: str
    ) -> None:
        if s.expected_cop <= 0:
            return
        assert self._canvas is not None
        x0, _, x1, _ = box
        y = self._y_for(box, s.expected_cop, peak)
        self._canvas.create_line(x0, y, x1, y, fill=color, width=2, dash=(6, 4))
        cap = f"Presupuesto: {self._format_short(s.expected_cop)}"
        self._canvas.create_text(x1, y - 8, text=cap, fill=color, anchor="e", font=("Segoe UI", 9, "bold"))

    def _draw_polyline(
        self, pts: list[tuple[float, float, float]], color: str, width: int
    ) -> None:
        if len(pts) < 2:
            return
        assert self._canvas is not None
        flat: list[float] = []
        for x, y, _ in pts:
            flat.extend([x, y])
        self._canvas.create_line(*flat, fill=color, width=width, smooth=False, capstyle="round")

    def _draw_markers(
        self, pts: list[tuple[float, float, float]], s: LinkedPairSeries, color: str
    ) -> None:
        assert self._canvas is not None
        for x, y, v in pts:
            ring = BudgetUiTheme.RED if (s.expected_cop > 0 and v > s.expected_cop) else color
            self._canvas.create_oval(x - 5, y - 5, x + 5, y + 5, fill=BudgetUiTheme.BG_CARD, outline=ring, width=3)

    def _draw_focus_caption(
        self, box: tuple[float, float, float, float], s: LinkedPairSeries, color: str
    ) -> None:
        assert self._canvas is not None
        x0, y0, _, _ = box
        cap = f"Real · {s.label_path}"
        self._canvas.create_text(x0, y0 - 8, text=cap, fill=color, anchor="sw", font=("Segoe UI", 11, "bold"))

    def _draw_multi_caption(self, box: tuple[float, float, float, float]) -> None:
        assert self._canvas is not None
        x0, y0, _, _ = box
        cap = "Líneas: gasto real por categoría enlazada"
        self._canvas.create_text(x0, y0 - 8, text=cap, fill=BudgetUiTheme.TXT_SEC, anchor="sw", font=("Segoe UI", 10))
