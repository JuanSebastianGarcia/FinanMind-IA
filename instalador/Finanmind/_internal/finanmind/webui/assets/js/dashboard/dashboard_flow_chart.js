import { DomBuilder } from "../core/dom_builder.js";

const SVG_NS = "http://www.w3.org/2000/svg";

export class DashboardFlowChart {
  /** Grouped-bar SVG chart with income vs distribution per month. */
  constructor(points) {
    this._points = Array.isArray(points) ? points : [];
  }

  build() {
    const card = DomBuilder.el("div", "dash-card");
    card.appendChild(DomBuilder.el("div", "dash-card__title", "Flujo mensual (ingresos vs asignaciones)"));
    card.appendChild(this._buildHint());
    card.appendChild(this._buildChart());
    return card;
  }

  _buildHint() {
    return DomBuilder.el(
      "div",
      "dash-flow__hint",
      "Barras azules: ingresos del mes · Barras grises: dinero asignado a etiquetas del presupuesto",
    );
  }

  _buildChart() {
    const svg = document.createElementNS(SVG_NS, "svg");
    svg.setAttribute("class", "dash-flow__svg");
    svg.setAttribute("viewBox", "0 0 600 240");
    svg.setAttribute("preserveAspectRatio", "none");
    if (this._points.length === 0) this._paintEmpty(svg);
    else this._paintBars(svg);
    return svg;
  }

  _paintEmpty(svg) {
    const text = document.createElementNS(SVG_NS, "text");
    text.setAttribute("x", "300");
    text.setAttribute("y", "120");
    text.setAttribute("text-anchor", "middle");
    text.setAttribute("fill", "#9ca3af");
    text.setAttribute("font-size", "12");
    text.textContent = "Añade ingresos o asignaciones para ver la tendencia";
    svg.appendChild(text);
  }

  _paintBars(svg) {
    const layout = this._layout();
    for (let i = 0; i < this._points.length; i += 1) {
      this._paintMonth(svg, layout, i);
    }
  }

  _layout() {
    const peak = this._peak();
    const slot = (600 - 32) / this._points.length;
    const barWidth = Math.max(slot * 0.28, 8);
    return { peak, slot, barWidth, baseY: 240 - 36, usable: (240 - 36) - 28 };
  }

  _peak() {
    let max = 1;
    for (const point of this._points) {
      max = Math.max(max, point.income_cop || 0, point.distribution_cop || 0);
    }
    return max;
  }

  _paintMonth(svg, layout, index) {
    const point = this._points[index];
    const centerX = 16 + layout.slot * (index + 0.5);
    this._paintBar(svg, centerX - layout.barWidth - 2, layout, point.income_cop || 0, "var(--accent)");
    this._paintBar(svg, centerX + 2, layout, point.distribution_cop || 0, "#6b7280");
    this._paintMonthLabel(svg, centerX, point.month_key || "");
  }

  _paintBar(svg, x, layout, value, color) {
    const height = layout.peak <= 0 ? 0 : Math.min(layout.usable, (value / layout.peak) * layout.usable);
    const y = layout.baseY - height;
    const rect = document.createElementNS(SVG_NS, "rect");
    rect.setAttribute("x", String(x));
    rect.setAttribute("y", String(y));
    rect.setAttribute("width", String(layout.barWidth));
    rect.setAttribute("height", String(height));
    rect.setAttribute("fill", color);
    svg.appendChild(rect);
  }

  _paintMonthLabel(svg, centerX, monthKey) {
    const text = document.createElementNS(SVG_NS, "text");
    text.setAttribute("x", String(centerX));
    text.setAttribute("y", "228");
    text.setAttribute("text-anchor", "middle");
    text.setAttribute("fill", "#9ca3af");
    text.setAttribute("font-size", "10");
    text.textContent = monthKey.length >= 7 ? monthKey.slice(5) : monthKey;
    svg.appendChild(text);
  }
}
