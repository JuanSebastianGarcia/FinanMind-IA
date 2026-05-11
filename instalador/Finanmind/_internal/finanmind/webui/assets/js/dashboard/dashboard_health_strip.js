import { DomBuilder } from "../core/dom_builder.js";

export class DashboardHealthStrip {
  /** Row of coloured pills (ok / warn / bad) summarising overall health. */
  constructor(rows) {
    this._rows = Array.isArray(rows) ? rows : [];
  }

  build() {
    const block = DomBuilder.el("div", "dash-health");
    block.appendChild(DomBuilder.el("div", "dash-health__title", "Estado visual"));
    block.appendChild(this._buildRow());
    return block;
  }

  _buildRow() {
    const row = DomBuilder.el("div", "dash-health__row");
    for (const item of this._rows) row.appendChild(this._buildPill(item));
    return row;
  }

  _buildPill(item) {
    const className = DashboardHealthStrip._classFor(item.tone);
    return DomBuilder.el("div", `dash-health__pill ${className}`, item.caption || "");
  }

  static _classFor(tone) {
    if (tone === "bad") return "dash-health__pill--bad";
    if (tone === "warn") return "dash-health__pill--warn";
    return "dash-health__pill--ok";
  }
}
