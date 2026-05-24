import { CurrencyFormatter } from "../format/currency_formatter.js";
import { DomBuilder } from "../core/dom_builder.js";

export class CardExpensesTable {
  /** Lists every charge for the active cycle with running totals and row actions. */
  constructor(rows, handlers) {
    this._rows = rows || [];
    this._handlers = handlers;
  }

  build() {
    const scroll = DomBuilder.el("div", "detail__card-scroll");
    if (this._rows.length === 0) {
      scroll.appendChild(DomBuilder.el("div", "detail__empty", "Sin movimientos en este ciclo."));
      return scroll;
    }
    const container = DomBuilder.el("div", "exp-table");
    container.appendChild(this._buildHeader());
    for (const row of this._rows) container.appendChild(this._buildRow(row));
    scroll.appendChild(container);
    return scroll;
  }

  _buildHeader() {
    const head = DomBuilder.el("div", "exp-table__header");
    head.appendChild(DomBuilder.el("div", "exp-table__cell-date", "Fecha"));
    head.appendChild(DomBuilder.el("div", "exp-table__cell-desc", "Descripción"));
    head.appendChild(DomBuilder.el("div", "exp-table__cell-cat", "Categoría"));
    head.appendChild(DomBuilder.el("div", "exp-table__cell-amount", "Valor"));
    head.appendChild(DomBuilder.el("div", "exp-table__cell-running", "Acumulado"));
    head.appendChild(DomBuilder.el("div", "exp-table__cell-actions"));
    return head;
  }

  _buildRow(row) {
    const node = DomBuilder.el("div", "exp-table__row");
    node.appendChild(DomBuilder.el("div", "exp-table__cell-date", row.occurred_on));
    node.appendChild(this._buildDescCell(row));
    node.appendChild(DomBuilder.el("div", "exp-table__cell-cat", row.category_caption));
    node.appendChild(this._buildAmountCell(row));
    node.appendChild(DomBuilder.el("div", "exp-table__cell-running", CurrencyFormatter.formatCop(row.running_total_cop)));
    node.appendChild(this._buildActions(row.expense_id));
    return node;
  }

  _buildDescCell(row) {
    const cell = DomBuilder.el("div", "exp-table__cell-desc");
    const desc = DomBuilder.el("span", null, row.description || "—");
    cell.appendChild(desc);
    return cell;
  }

  _buildAmountCell(row) {
    const cell = DomBuilder.el("div", "exp-table__cell-amount");
    cell.appendChild(DomBuilder.el("span", null, CurrencyFormatter.formatCop(row.amount_cop)));

    const isFirst = row.installment_number === 1 && row.installments > 1;
    if (isFirst && row.total_amount_cop > 0) {
      const hint = DomBuilder.el("div", "exp-table__installment-hint",
        `Total: ${CurrencyFormatter.formatCop(row.total_amount_cop)} · ${row.installments} cuotas`);
      cell.appendChild(hint);
    }
    return cell;
  }

  _buildActions(expenseId) {
    const cell = DomBuilder.el("div", "exp-table__cell-actions");
    cell.appendChild(DomBuilder.button("exp-table__btn", "Editar", () => this._handlers.onEdit(expenseId)));
    cell.appendChild(DomBuilder.button("exp-table__btn exp-table__btn--danger", "Quitar", () => this._handlers.onDelete(expenseId)));
    return cell;
  }
}
