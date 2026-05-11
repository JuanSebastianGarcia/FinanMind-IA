import { DomBuilder } from "../core/dom_builder.js";
import { InvestmentRow } from "./investment_row.js";

export class InvestmentsList {
  /** Scrollable list of investment rows; renders an empty state when empty. */
  constructor(entries, handlers) {
    this._entries = Array.isArray(entries) ? entries : [];
    this._handlers = handlers || {};
  }

  build() {
    const host = DomBuilder.el("div", "invest__col-scroll");
    if (this._entries.length === 0) {
      host.appendChild(this._buildEmpty());
      return host;
    }
    for (const entry of this._entries) {
      host.appendChild(new InvestmentRow(entry, this._handlers).build());
    }
    return host;
  }

  _buildEmpty() {
    const wrap = DomBuilder.el("div", "invest__empty");
    wrap.appendChild(DomBuilder.el("div", "invest__empty-title", "Sin inversiones registradas"));
    wrap.appendChild(DomBuilder.el(
      "div",
      "invest__empty-body",
      "Añade categorías y luego registra montos por categoría.",
    ));
    return wrap;
  }
}
