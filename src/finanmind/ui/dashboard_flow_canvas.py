"""Grouped bar canvas for income vs budget assignments by month."""

from __future__ import annotations

import tkinter as tk

import customtkinter as ctk

from finanmind.ui.budget_ui_theme import BudgetUiTheme


class DashboardFlowCanvas:
    """Draws paired columns per month with soft colors and captions."""

    def __init__(self, parent: ctk.CTkFrame) -> None:
        self._parent = parent
        self._canvas: tk.Canvas | None = None
        self._points: list[tuple[str, float, float]] = []

    def attach(self) -> None:
        """Create the canvas and bind resize redraws."""
        bg = BudgetUiTheme.BG_CARD
        canvas = tk.Canvas(self._parent, height=240, bg=bg, highlightthickness=0, bd=0)
        canvas.pack(fill="both", expand=True, padx=10, pady=8)
        canvas.bind("<Configure>", self._on_cfg)
        self._canvas = canvas

    def set_points(self, points: list[tuple[str, float, float]]) -> None:
        """Replace series ``(yyyy-mm, income, assignments)`` and redraw."""
        self._points = list(points)
        self._redraw()

    def _on_cfg(self, _event: object) -> None:
        self._redraw()

    def _redraw(self) -> None:
        if self._canvas is None:
            return
        self._canvas.delete("all")
        w = float(self._canvas.winfo_width())
        h = float(self._canvas.winfo_height())
        if w < 40 or h < 40:
            return
        if not self._points:
            self._draw_empty(w, h)
            return
        top = self._max_pair()
        self._draw_pairs(w, h, top)

    def _draw_empty(self, w: float, h: float) -> None:
        assert self._canvas is not None
        self._canvas.create_text(
            w / 2,
            h / 2,
            text="Añade ingresos o asignaciones para ver la tendencia",
            fill=BudgetUiTheme.TXT_TER,
            font=("Segoe UI", 12),
        )

    def _max_pair(self) -> float:
        peak = 1.0
        for _, inc, dist in self._points:
            peak = max(peak, inc, dist)
        return peak

    def _draw_pairs(self, w: float, h: float, top: float) -> None:
        assert self._canvas is not None
        pad = 36.0
        base = h - pad
        span = max(w - 24.0, 10.0)
        n = len(self._points)
        slot = span / float(n)
        bar_w = max(slot * 0.28, 8.0)
        for i, (mk, inc, dist) in enumerate(self._points):
            cx = 16.0 + slot * (i + 0.5)
            self._bar(self._canvas, cx - bar_w - 2, base, bar_w, inc, top, BudgetUiTheme.ACCENT)
            self._bar(self._canvas, cx + 2, base, bar_w, dist, top, BudgetUiTheme.TXT_SEC)
            self._canvas.create_text(cx, h - 12, text=mk[5:], fill=BudgetUiTheme.TXT_TER, font=("Segoe UI", 9))

    def _bar(self, canvas: tk.Canvas, x: float, base: float, bw: float, val: float, top: float, color: str) -> None:
        usable = base - 28.0
        hgt = 0.0 if top <= 0 else min(usable, (val / top) * usable)
        y0 = base - hgt
        canvas.create_rectangle(x, y0, x + bw, base, fill=color, outline="", width=0)
