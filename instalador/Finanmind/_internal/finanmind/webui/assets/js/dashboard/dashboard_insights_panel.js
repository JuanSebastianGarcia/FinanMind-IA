import { DomBuilder } from "../core/dom_builder.js";

export class DashboardInsightsPanel {
  /** Bulleted list of soft-spoken insights produced by the snapshot. */
  constructor(lines) {
    this._lines = Array.isArray(lines) ? lines : [];
  }

  build() {
    const card = DomBuilder.el("div", "dash-insights");
    card.appendChild(DomBuilder.el("div", "dash-insights__title", "Insights automáticos"));
    if (this._lines.length === 0) {
      card.appendChild(this._buildEmpty());
      return card;
    }
    for (const line of this._lines) card.appendChild(this._buildLine(line));
    return card;
  }

  _buildEmpty() {
    return DomBuilder.el(
      "div",
      "dash-insights__empty",
      "Cuando haya más historia mensual aparecerán comparaciones aquí.",
    );
  }

  _buildLine(text) {
    return DomBuilder.el("div", "dash-insights__line", `• ${text}`);
  }
}
