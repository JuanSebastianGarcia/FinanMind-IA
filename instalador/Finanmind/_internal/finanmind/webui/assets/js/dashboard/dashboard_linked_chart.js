import { DashboardShortAmountFormatter } from "./dashboard_short_amount_formatter.js";

const SVG_NS = "http://www.w3.org/2000/svg";

export class DashboardLinkedChart {
  /** SVG line chart comparing actual CC spend vs budget per linked pair. */
  constructor(series, focusId, span, anchor) {
    this._series = Array.isArray(series) ? series : [];
    this._focusId = focusId || "";
    this._span = Math.max(1, Number(span) || 6);
    this._anchor = anchor || "";
  }

  build() {
    const svg = document.createElementNS(SVG_NS, "svg");
    svg.setAttribute("class", "dash-linked__chart");
    svg.setAttribute("viewBox", "0 0 900 220");
    if (this._series.length === 0) this._paintEmpty(svg);
    else this._paintChart(svg);
    return svg;
  }

  _paintEmpty(svg) {
    const text = document.createElementNS(SVG_NS, "text");
    text.setAttribute("x", "450");
    text.setAttribute("y", "110");
    text.setAttribute("text-anchor", "middle");
    text.setAttribute("fill", "#9ca3af");
    text.setAttribute("font-size", "12");
    text.textContent = "Enlaza una etiqueta del presupuesto a una categoría de tarjeta para verla aquí";
    svg.appendChild(text);
  }

  _paintChart(svg) {
    const months = this._visibleMonths();
    const focus = this._focusSeries();
    const targets = focus ? [focus] : this._series;
    const peak = this._peak(targets, months);
    const box = { x0: 60, y0: 24, x1: 900 - 18, y1: 220 - 28 };
    this._paintAxes(svg, box, peak, months);
    if (focus) this._paintSingle(svg, box, focus, months, peak);
    else this._paintMulti(svg, box, months, peak);
  }

  _visibleMonths() {
    if (this._series.length === 0) return [];
    const all = this._series[0].points || [];
    const keys = all.map((p) => p.month_key);
    return keys.length > this._span ? keys.slice(-this._span) : keys;
  }

  _focusSeries() {
    if (!this._focusId) return null;
    return this._series.find((s) => s.pair_id === this._focusId) || null;
  }

  _peak(targets, months) {
    let max = 1;
    for (const s of targets) {
      for (const p of s.points || []) {
        if (months.includes(p.month_key)) max = Math.max(max, Number(p.value_cop) || 0);
      }
      max = Math.max(max, Number(s.expected_cop) || 0);
    }
    return max * 1.1;
  }

  _paintAxes(svg, box, peak, months) {
    this._paintGrid(svg, box);
    this._paintYLabels(svg, box, peak);
    this._paintXLabels(svg, box, months);
  }

  _paintGrid(svg, box) {
    for (const fr of [0, 0.5, 1]) {
      const y = box.y1 - (box.y1 - box.y0) * fr;
      const line = document.createElementNS(SVG_NS, "line");
      line.setAttribute("x1", String(box.x0));
      line.setAttribute("x2", String(box.x1));
      line.setAttribute("y1", String(y));
      line.setAttribute("y2", String(y));
      line.setAttribute("stroke", "#e5e7eb");
      line.setAttribute("stroke-dasharray", "2 3");
      svg.appendChild(line);
    }
  }

  _paintYLabels(svg, box, peak) {
    for (const fr of [0, 0.5, 1]) {
      const y = box.y1 - (box.y1 - box.y0) * fr;
      const text = document.createElementNS(SVG_NS, "text");
      text.setAttribute("x", String(box.x0 - 8));
      text.setAttribute("y", String(y + 3));
      text.setAttribute("text-anchor", "end");
      text.setAttribute("fill", "#9ca3af");
      text.setAttribute("font-size", "10");
      text.textContent = DashboardShortAmountFormatter.format(peak * fr);
      svg.appendChild(text);
    }
  }

  _paintXLabels(svg, box, months) {
    for (let i = 0; i < months.length; i += 1) {
      const x = this._xFor(box, i, months.length);
      const text = document.createElementNS(SVG_NS, "text");
      text.setAttribute("x", String(x));
      text.setAttribute("y", String(box.y1 + 14));
      text.setAttribute("text-anchor", "middle");
      text.setAttribute("fill", "#9ca3af");
      text.setAttribute("font-size", "10");
      text.textContent = DashboardLinkedChart._shortMonth(months[i]);
      svg.appendChild(text);
    }
  }

  static _shortMonth(mk) {
    if (!mk || mk.length < 7) return mk || "";
    const monthIdx = parseInt(mk.slice(5, 7), 10) - 1;
    const names = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"];
    if (monthIdx < 0 || monthIdx >= 12) return mk;
    return names[monthIdx];
  }

  _xFor(box, idx, count) {
    if (count <= 1) return (box.x0 + box.x1) / 2;
    return box.x0 + ((box.x1 - box.x0) * idx) / (count - 1);
  }

  _yFor(box, value, peak) {
    if (peak <= 0) return box.y1;
    const fr = Math.max(0, Math.min(1, (Number(value) || 0) / peak));
    return box.y1 - (box.y1 - box.y0) * fr;
  }

  _paintSingle(svg, box, series, months, peak) {
    const color = series.color || "#1d4ed8";
    const pts = this._pointsFor(box, series, months, peak);
    this._paintBudgetLine(svg, box, series, peak, color);
    this._paintPolyline(svg, pts, color, 4);
    this._paintMarkers(svg, pts, series, color);
    this._paintFocusCaption(svg, box, series, color);
  }

  _paintMulti(svg, box, months, peak) {
    for (const s of this._series) {
      const pts = this._pointsFor(box, s, months, peak);
      this._paintPolyline(svg, pts, s.color || "#1d4ed8", 3);
    }
    this._paintMultiCaption(svg, box);
  }

  _pointsFor(box, series, months, peak) {
    const map = new Map();
    for (const p of series.points || []) map.set(p.month_key, Number(p.value_cop) || 0);
    return months.map((m, idx) => ({
      x: this._xFor(box, idx, months.length),
      y: this._yFor(box, map.get(m) || 0, peak),
      v: map.get(m) || 0,
    }));
  }

  _paintBudgetLine(svg, box, series, peak, color) {
    if ((series.expected_cop || 0) <= 0) return;
    const y = this._yFor(box, series.expected_cop, peak);
    const line = document.createElementNS(SVG_NS, "line");
    line.setAttribute("x1", String(box.x0));
    line.setAttribute("x2", String(box.x1));
    line.setAttribute("y1", String(y));
    line.setAttribute("y2", String(y));
    line.setAttribute("stroke", color);
    line.setAttribute("stroke-width", "2");
    line.setAttribute("stroke-dasharray", "6 4");
    svg.appendChild(line);
    this._paintBudgetCaption(svg, box, series.expected_cop, y, color);
  }

  _paintBudgetCaption(svg, box, expected, y, color) {
    const text = document.createElementNS(SVG_NS, "text");
    text.setAttribute("x", String(box.x1));
    text.setAttribute("y", String(y - 6));
    text.setAttribute("text-anchor", "end");
    text.setAttribute("fill", color);
    text.setAttribute("font-size", "10");
    text.setAttribute("font-weight", "700");
    text.textContent = `Presupuesto: ${DashboardShortAmountFormatter.format(expected)}`;
    svg.appendChild(text);
  }

  _paintPolyline(svg, pts, color, width) {
    if (pts.length < 2) return;
    const path = pts.map((p, idx) => `${idx === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ");
    const node = document.createElementNS(SVG_NS, "path");
    node.setAttribute("d", path);
    node.setAttribute("fill", "none");
    node.setAttribute("stroke", color);
    node.setAttribute("stroke-width", String(width));
    node.setAttribute("stroke-linecap", "round");
    node.setAttribute("stroke-linejoin", "round");
    svg.appendChild(node);
  }

  _paintMarkers(svg, pts, series, color) {
    const expected = Number(series.expected_cop) || 0;
    for (const p of pts) {
      const ring = expected > 0 && p.v > expected ? "#ef4444" : color;
      const circle = document.createElementNS(SVG_NS, "circle");
      circle.setAttribute("cx", String(p.x));
      circle.setAttribute("cy", String(p.y));
      circle.setAttribute("r", "5");
      circle.setAttribute("fill", "#ffffff");
      circle.setAttribute("stroke", ring);
      circle.setAttribute("stroke-width", "3");
      svg.appendChild(circle);
    }
  }

  _paintFocusCaption(svg, box, series, color) {
    const text = document.createElementNS(SVG_NS, "text");
    text.setAttribute("x", String(box.x0));
    text.setAttribute("y", String(box.y0 - 8));
    text.setAttribute("fill", color);
    text.setAttribute("font-size", "12");
    text.setAttribute("font-weight", "700");
    text.textContent = `Real · ${series.label_path}`;
    svg.appendChild(text);
  }

  _paintMultiCaption(svg, box) {
    const text = document.createElementNS(SVG_NS, "text");
    text.setAttribute("x", String(box.x0));
    text.setAttribute("y", String(box.y0 - 8));
    text.setAttribute("fill", "#6b7280");
    text.setAttribute("font-size", "11");
    text.textContent = "Líneas: gasto real por categoría enlazada";
    svg.appendChild(text);
  }
}
