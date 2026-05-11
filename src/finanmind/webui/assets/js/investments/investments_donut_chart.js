const SVG_NS = "http://www.w3.org/2000/svg";

export class InvestmentsDonutChart {
  /** Renders a donut ring with one slice per row using SVG paths. */
  constructor(rows, size = 240) {
    this._rows = Array.isArray(rows) ? rows : [];
    this._size = Math.max(120, Number(size) || 240);
  }

  build() {
    const host = document.createElement("div");
    host.className = "invest-donut";
    if (this._rows.length === 0) {
      host.appendChild(this._buildEmptyHint());
      return host;
    }
    host.appendChild(this._buildSvg());
    return host;
  }

  _buildEmptyHint() {
    const hint = document.createElement("div");
    hint.className = "invest-donut__hint";
    hint.textContent = "Sin datos para esta moneda";
    return hint;
  }

  _buildSvg() {
    const svg = document.createElementNS(SVG_NS, "svg");
    svg.setAttribute("viewBox", "0 0 100 100");
    svg.setAttribute("class", "invest-donut__svg");
    this._paintSlices(svg);
    return svg;
  }

  _paintSlices(svg) {
    let start = -90;
    for (const row of this._rows) {
      const sweep = (row.share_ratio || 0) * 360;
      if (sweep <= 0) continue;
      svg.appendChild(this._buildArc(start, sweep, row.color || "#4f8ef7"));
      if (sweep >= 11) svg.appendChild(this._buildLabel(start, sweep, row));
      start += sweep;
    }
  }

  _buildArc(startDeg, sweepDeg, color) {
    const path = document.createElementNS(SVG_NS, "path");
    path.setAttribute("d", InvestmentsDonutChart._arcPath(startDeg, sweepDeg));
    path.setAttribute("fill", color);
    path.setAttribute("stroke", "#ffffff");
    path.setAttribute("stroke-width", "1");
    return path;
  }

  _buildLabel(startDeg, sweepDeg, row) {
    const midDeg = startDeg + sweepDeg / 2;
    const rad = (midDeg * Math.PI) / 180;
    const r = 33;
    const x = 50 + r * Math.cos(rad);
    const y = 50 + r * Math.sin(rad);
    const text = document.createElementNS(SVG_NS, "text");
    text.setAttribute("x", String(x));
    text.setAttribute("y", String(y));
    text.setAttribute("text-anchor", "middle");
    text.setAttribute("dominant-baseline", "central");
    text.setAttribute("font-size", "5.5");
    text.setAttribute("font-weight", "700");
    text.setAttribute("fill", InvestmentsDonutChart._labelFill(row.color || "#4f8ef7"));
    text.textContent = `${Math.round((row.share_ratio || 0) * 100)}%`;
    return text;
  }

  static _arcPath(startDeg, sweepDeg) {
    const ro = 42;
    const ri = ro * 0.58;
    const endDeg = startDeg + Math.min(sweepDeg, 359.99);
    const xs1 = 50 + ro * Math.cos((startDeg * Math.PI) / 180);
    const ys1 = 50 + ro * Math.sin((startDeg * Math.PI) / 180);
    const xs2 = 50 + ro * Math.cos((endDeg * Math.PI) / 180);
    const ys2 = 50 + ro * Math.sin((endDeg * Math.PI) / 180);
    const xi2 = 50 + ri * Math.cos((endDeg * Math.PI) / 180);
    const yi2 = 50 + ri * Math.sin((endDeg * Math.PI) / 180);
    const xi1 = 50 + ri * Math.cos((startDeg * Math.PI) / 180);
    const yi1 = 50 + ri * Math.sin((startDeg * Math.PI) / 180);
    const large = sweepDeg > 180 ? 1 : 0;
    return [
      `M ${xs1} ${ys1}`,
      `A ${ro} ${ro} 0 ${large} 1 ${xs2} ${ys2}`,
      `L ${xi2} ${yi2}`,
      `A ${ri} ${ri} 0 ${large} 0 ${xi1} ${yi1}`,
      "Z",
    ].join(" ");
  }

  static _labelFill(hex) {
    const raw = String(hex || "").replace("#", "");
    if (raw.length !== 6) return "#ffffff";
    const r = parseInt(raw.slice(0, 2), 16);
    const g = parseInt(raw.slice(2, 4), 16);
    const b = parseInt(raw.slice(4, 6), 16);
    const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
    return luminance > 0.72 ? "#111827" : "#ffffff";
  }
}
