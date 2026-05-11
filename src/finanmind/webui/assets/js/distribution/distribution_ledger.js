import { CurrencyFormatter } from "../format/currency_formatter.js";
import { DomBuilder } from "../core/dom_builder.js";

export class DistributionLedger {
  /** Renders the receipt's income row plus its allocation rows with running balance. */
  constructor(host, handlers) {
    this._host = host;
    this._handlers = handlers;
    this._scroll = null;
  }

  mount() {
    const column = DomBuilder.el("div", "distribution__column");
    column.appendChild(DomBuilder.el("div", "distribution__column-title", "Movimientos del ingreso"));
    this._scroll = DomBuilder.el("div", "distribution__card-scroll");
    column.appendChild(this._scroll);
    this._host.appendChild(column);
  }

  update(rows, hasReceipt) {
    this._scroll.innerHTML = "";
    if (!hasReceipt) {
      this._scroll.appendChild(DomBuilder.el("div", "ledger__empty", "No hay ingreso seleccionado."));
      return;
    }
    const container = DomBuilder.el("div", "ledger");
    container.appendChild(this._buildHeader());
    for (const row of rows) container.appendChild(this._renderRow(row));
    this._scroll.appendChild(container);
  }

  _renderRow(row) {
    if (row.kind === "income") return this._buildIncomeRow(row);
    return this._buildLineRow(row);
  }

  _buildHeader() {
    const head = DomBuilder.el("div", "ledger__header");
    head.appendChild(DomBuilder.el("div", "ledger__cell-action"));
    head.appendChild(DomBuilder.el("div", "ledger__cell-date", "Fecha"));
    head.appendChild(DomBuilder.el("div", "ledger__cell-concept", "Concepto"));
    head.appendChild(DomBuilder.el("div", "ledger__cell-amount", "Monto"));
    head.appendChild(DomBuilder.el("div", "ledger__cell-balance", "Saldo ingreso"));
    return head;
  }

  _buildIncomeRow(row) {
    const node = DomBuilder.el("div", "ledger__row ledger__row--income");
    node.appendChild(DomBuilder.el("div", "ledger__cell-action"));
    node.appendChild(DomBuilder.el("div", "ledger__cell-date", row.occurred_on));
    node.appendChild(DomBuilder.el("div", "ledger__cell-concept", DistributionLedger._incomeConcept(row)));
    node.appendChild(DomBuilder.el("div", "ledger__cell-amount", CurrencyFormatter.formatCop(row.amount_cop)));
    node.appendChild(DomBuilder.el("div", "ledger__cell-balance", CurrencyFormatter.formatCop(row.balance_cop)));
    return node;
  }

  _buildLineRow(row) {
    const node = DomBuilder.el("div", "ledger__row");
    node.appendChild(this._buildRemoveCell(row.id));
    node.appendChild(DomBuilder.el("div", "ledger__cell-date", row.occurred_on));
    node.appendChild(DomBuilder.el("div", "ledger__cell-concept", DistributionLedger._lineConcept(row)));
    node.appendChild(DomBuilder.el("div", "ledger__cell-amount", CurrencyFormatter.formatCop(row.amount_cop)));
    node.appendChild(this._buildBalanceCell(row.balance_cop));
    return node;
  }

  _buildRemoveCell(lineId) {
    const cell = DomBuilder.el("div", "ledger__cell-action");
    cell.appendChild(DomBuilder.button("ledger__remove-btn", "Quitar", () => this._handlers.onDeleteLine(lineId)));
    return cell;
  }

  _buildBalanceCell(balanceCop) {
    const cell = DomBuilder.el("div", "ledger__cell-balance", CurrencyFormatter.formatCop(balanceCop));
    if (balanceCop < 0) cell.classList.add("ledger__cell-balance--negative");
    return cell;
  }

  static _incomeConcept(row) {
    const memo = (row.memo || "").trim();
    return memo ? `Ingreso · ${memo}` : "Ingreso registrado";
  }

  static _lineConcept(row) {
    const title = (row.label_title || "Etiqueta").trim();
    const memo = (row.memo || "").trim();
    return memo === "" ? title : `${title} · ${memo}`;
  }
}
