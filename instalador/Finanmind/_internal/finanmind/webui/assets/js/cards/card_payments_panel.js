import { CurrencyFormatter } from "../format/currency_formatter.js";
import { DomBuilder } from "../core/dom_builder.js";

export class CardPaymentsPanel {
  /** Right-side payments list with date, amount, optional notes and Quitar button. */
  constructor(rows, handlers) {
    this._rows = rows || [];
    this._handlers = handlers;
  }

  build() {
    const scroll = DomBuilder.el("div", "detail__card-scroll");
    if (this._rows.length === 0) {
      scroll.appendChild(DomBuilder.el("div", "detail__empty", "Sin pagos registrados."));
      return scroll;
    }
    const container = DomBuilder.el("div", "pay-list");
    for (const row of this._rows) container.appendChild(this._buildRow(row));
    scroll.appendChild(container);
    return scroll;
  }

  _buildRow(row) {
    const node = DomBuilder.el("div", "pay-list__row");
    node.appendChild(this._buildTop(row));
    const notes = (row.notes || "").trim();
    if (notes !== "") {
      node.appendChild(DomBuilder.el("div", "pay-list__notes", notes));
    }
    return node;
  }

  _buildTop(row) {
    const top = DomBuilder.el("div", "pay-list__top");
    top.appendChild(DomBuilder.el("div", "pay-list__date", row.paid_on));
    top.appendChild(DomBuilder.el("div", "pay-list__amount", CurrencyFormatter.formatCop(row.amount_cop)));
    top.appendChild(DomBuilder.el("div", "pay-list__spacer"));
    top.appendChild(DomBuilder.button("pay-list__btn", "Quitar", () => this._handlers.onDelete(row.payment_id)));
    return top;
  }
}
