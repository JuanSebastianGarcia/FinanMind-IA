"""Tkinter donut chart: full ring, slice separation, and % labels on the ring."""

from __future__ import annotations

import math
import tkinter as tk

import customtkinter as ctk

from finanmind.ui.budget_ui_theme import BudgetUiTheme
from finanmind.ui.investment_chart_palette import InvestmentChartPalette


class InvestmentDonutCanvas:
    """Draws category slices on a square canvas with a short sweep-in animation."""

    def __init__(self, parent: ctk.CTkFrame, size: int = 280) -> None:
        self._parent = parent
        self._canvas: tk.Canvas | None = None
        self._job: str | None = None
        self._rows: list[tuple[str, float, float]] = []
        self._progress = 1.0
        self._size = max(120, int(size))

    def attach(self) -> None:
        """Create a fixed square canvas so the ring is always circular."""
        bg = BudgetUiTheme.BG_CARD
        canvas = tk.Canvas(
            self._parent,
            width=self._size,
            height=self._size,
            bg=bg,
            highlightthickness=0,
            bd=0,
        )
        canvas.pack(anchor="center", pady=(4, 6))
        canvas.bind("<Configure>", self._on_resize)
        self._canvas = canvas

    def _on_resize(self, _event: object) -> None:
        if self._canvas is None or self._progress < 1.0:
            return
        self._redraw()

    def set_slices(self, rows: list[tuple[str, float, float]]) -> None:
        """Accept ``(label, amount, share)`` rows and restart the sweep."""
        self._rows = list(rows)
        self._progress = 0.0
        self._restart_animation()

    def _restart_animation(self) -> None:
        self._cancel_job()
        self._tick()

    def _cancel_job(self) -> None:
        if self._canvas is None or self._job is None:
            return
        self._canvas.after_cancel(self._job)
        self._job = None

    def _tick(self) -> None:
        assert self._canvas is not None
        self._progress = min(1.0, self._progress + 0.09)
        self._redraw()
        if self._progress < 1.0:
            self._job = self._canvas.after(26, self._tick)

    def _redraw(self) -> None:
        assert self._canvas is not None
        self._canvas.delete("all")
        w = max(float(self._canvas.winfo_width()), float(self._size))
        h = max(float(self._canvas.winfo_height()), float(self._size))
        side = min(w, h)
        cx, cy = w / 2.0, h / 2.0
        ro = side * 0.42
        ri = ro * 0.58
        if not self._rows:
            self._draw_placeholder(cx, cy, ro)
            return
        start = -90.0
        slice_meta: list[tuple[float, float, float, int]] = []
        slice_count = len(self._rows)
        for i, row in enumerate(self._rows):
            _label, _amt, share = row
            extent = share * 360.0 * self._progress
            color = InvestmentChartPalette.color_at(i)
            self._paint_slice(cx, cy, ro, start, extent, color, slice_count)
            slice_meta.append((start, extent, share, i))
            start += extent
        self._punch_hole(cx, cy, ri)
        for start_a, extent, share, idx in slice_meta:
            self._maybe_draw_pct(cx, cy, ro, ri, start_a, extent, share, idx)

    def _draw_placeholder(self, cx: float, cy: float, ro: float) -> None:
        assert self._canvas is not None
        self._canvas.create_oval(cx - ro, cy - ro, cx + ro, cy + ro, outline=BudgetUiTheme.BORDER, width=2)

    def _paint_slice(
        self,
        cx: float,
        cy: float,
        ro: float,
        start: float,
        extent: float,
        color: str,
        slice_count: int,
    ) -> None:
        assert self._canvas is not None
        if extent <= 0.08:
            return
        draw_extent = self._tk_safe_extent(extent, slice_count)
        x0, y0 = cx - ro, cy - ro
        x1, y1 = cx + ro, cy + ro
        self._canvas.create_arc(
            x0,
            y0,
            x1,
            y1,
            start=start,
            extent=draw_extent,
            fill=color,
            outline="#ffffff",
            width=2,
            style=tk.PIESLICE,
        )

    def _tk_safe_extent(self, extent: float, slice_count: int) -> float:
        """Tkinter often skips a full 360° pie slice; cap slightly below for one slice."""
        if slice_count == 1 and extent >= 359.0:
            return 359.99
        return extent

    def _punch_hole(self, cx: float, cy: float, ri: float) -> None:
        assert self._canvas is not None
        fill = BudgetUiTheme.BG_CARD
        self._canvas.create_oval(cx - ri, cy - ri, cx + ri, cy + ri, fill=fill, outline=fill)

    def _maybe_draw_pct(
        self,
        cx: float,
        cy: float,
        ro: float,
        ri: float,
        start: float,
        extent: float,
        share: float,
        index: int,
    ) -> None:
        assert self._canvas is not None
        if extent < 11.0:
            return
        mid = start + extent * 0.5
        rad = math.radians(mid)
        rmid = (ro + ri) * 0.52
        x = cx + rmid * math.cos(rad)
        y = cy - rmid * math.sin(rad)
        text = f"{share * 100.0:.0f}%"
        fill = self._label_fill_for_slice(index)
        self._canvas.create_text(x, y, text=text, fill=fill, font=("Segoe UI", 10, "bold"))

    def _label_fill_for_slice(self, index: int) -> str:
        hex_color = InvestmentChartPalette.color_at(index)
        return BudgetUiTheme.TXT_PRI if self._is_light_hex(hex_color) else "#ffffff"

    def _is_light_hex(self, hex_color: str) -> bool:
        raw = hex_color.lstrip("#")
        if len(raw) != 6:
            return True
        try:
            r = int(raw[0:2], 16)
            g = int(raw[2:4], 16)
            b = int(raw[4:6], 16)
        except ValueError:
            return True
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
        return luminance > 0.72
