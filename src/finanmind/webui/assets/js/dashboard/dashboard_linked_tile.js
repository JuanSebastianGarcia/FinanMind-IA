import { CurrencyFormatter } from "../format/currency_formatter.js";
import { DomBuilder } from "../core/dom_builder.js";

export class DashboardLinkedTile {
  /** KPI tile for one linked pair showing real, budget and delta caption. */
  constructor(series, anchor) {
    this._series = series;
    this._anchor = anchor || "";
  }

  build() {
    const tile = DomBuilder.el("div", "dash-linked__tile");
    tile.appendChild(this._buildHeader());
    tile.appendChild(this._buildCardPath());
    tile.appendChild(this._buildReal());
    tile.appendChild(this._buildBudget());
    tile.appendChild(this._buildDelta());
    return tile;
  }

  _buildHeader() {
    return DomBuilder.el("div", "dash-linked__tile-label", this._series.label_path || "");
  }

  _buildCardPath() {
    const node = DomBuilder.el("div", "dash-linked__tile-card", `↪ ${this._series.card_category_path || ""}`);
    node.style.color = this._series.color || "var(--accent)";
    return node;
  }

  _buildReal() {
    const value = CurrencyFormatter.formatCop(this._actualForAnchor());
    return DomBuilder.el("div", "dash-linked__tile-real", `Real: ${value}`);
  }

  _buildBudget() {
    const value = CurrencyFormatter.formatCop(this._series.expected_cop || 0);
    return DomBuilder.el("div", "dash-linked__tile-budget", `Presupuesto: ${value}`);
  }

  _buildDelta() {
    const { text, color } = this._deltaInfo();
    const node = DomBuilder.el("div", "dash-linked__tile-delta", text);
    node.style.color = color;
    return node;
  }

  _actualForAnchor() {
    for (const point of this._series.points || []) {
      if (point.month_key === this._anchor) return point.value_cop || 0;
    }
    return 0;
  }

  _deltaInfo() {
    const expected = Number(this._series.expected_cop) || 0;
    const actual = this._actualForAnchor();
    if (expected <= 0) return { text: "Sin presupuesto definido", color: "var(--txt-ter)" };
    if (actual <= 0) return { text: "Sin gasto este mes", color: "var(--green)" };
    const deltaPct = ((actual - expected) / expected) * 100;
    if (actual > expected) return { text: `+${deltaPct.toFixed(0)}% sobre presupuesto`, color: "var(--red)" };
    if (deltaPct >= -5) return { text: `${deltaPct.toFixed(0)}% al límite`, color: "var(--amber)" };
    return { text: `${deltaPct.toFixed(0)}% bajo presupuesto`, color: "var(--green)" };
  }
}
