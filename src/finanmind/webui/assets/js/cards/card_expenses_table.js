import { CurrencyFormatter } from "../format/currency_formatter.js";
import { DomBuilder } from "../core/dom_builder.js";

export class CardExpensesTable {
  constructor(rows, handlers) {
    this._rows = rows || [];
    this._handlers = handlers;
    this._single = this._rows.filter(r => (r.installments || 1) <= 1);
    this._cuotas = this._rows.filter(r => (r.installments || 1) > 1);
  }

  build() {
    const wrap = DomBuilder.el("div", "exp-sections");

    if (this._rows.length === 0) {
      const scroll = DomBuilder.el("div", "detail__card-scroll");
      scroll.appendChild(DomBuilder.el("div", "detail__empty", "Sin movimientos en este ciclo."));
      wrap.appendChild(scroll);
      return wrap;
    }

    wrap.appendChild(this._buildSingleSection());
    wrap.appendChild(this._buildCuotasSection());
    return wrap;
  }

  // ── Gastos directos (1 cuota) ─────────────────────────────────────────────

  _buildSingleSection() {
    const section = DomBuilder.el("div", "exp-section");
    section.appendChild(DomBuilder.el("div", "detail__section-title", "Gastos directos"));
    if (this._single.length === 0) {
      section.appendChild(DomBuilder.el("div", "exp-section__empty", "Sin gastos directos este ciclo."));
    } else {
      const scroll = DomBuilder.el("div", "detail__card-scroll exp-section__scroll");
      const table = DomBuilder.el("div", "exp-table");
      table.appendChild(this._buildSingleHeader());
      for (const row of this._single) table.appendChild(this._buildSingleRow(row));
      scroll.appendChild(table);
      section.appendChild(scroll);
    }
    return section;
  }

  _buildSingleHeader() {
    const head = DomBuilder.el("div", "exp-table__header");
    head.appendChild(DomBuilder.el("div", "exp-table__cell-date", "Fecha"));
    head.appendChild(DomBuilder.el("div", "exp-table__cell-desc", "Descripción"));
    head.appendChild(DomBuilder.el("div", "exp-table__cell-cat", "Categoría"));
    head.appendChild(DomBuilder.el("div", "exp-table__cell-amount", "Valor"));
    head.appendChild(DomBuilder.el("div", "exp-table__cell-running", "Acumulado"));
    head.appendChild(DomBuilder.el("div", "exp-table__cell-actions"));
    return head;
  }

  _buildSingleRow(row) {
    const node = DomBuilder.el("div", "exp-table__row");
    node.appendChild(DomBuilder.el("div", "exp-table__cell-date", row.occurred_on));
    node.appendChild(this._buildDescCell(row));
    node.appendChild(DomBuilder.el("div", "exp-table__cell-cat", row.category_caption));
    node.appendChild(DomBuilder.el("div", "exp-table__cell-amount", CurrencyFormatter.formatCop(row.amount_cop)));
    node.appendChild(DomBuilder.el("div", "exp-table__cell-running", CurrencyFormatter.formatCop(row.running_total_cop)));
    node.appendChild(this._buildActions(row.expense_id));
    return node;
  }

  // ── Gastos a cuotas ───────────────────────────────────────────────────────

  _buildCuotasSection() {
    const section = DomBuilder.el("div", "exp-section");
    section.appendChild(DomBuilder.el("div", "detail__section-title", "Gastos a cuotas"));
    if (this._cuotas.length === 0) {
      section.appendChild(DomBuilder.el("div", "exp-section__empty", "Sin gastos a cuotas este ciclo."));
    } else {
      const scroll = DomBuilder.el("div", "detail__card-scroll exp-section__scroll");
      const table = DomBuilder.el("div", "exp-table");
      table.appendChild(this._buildCuotasHeader());
      for (const row of this._cuotas) table.appendChild(this._buildCuotaRow(row));
      scroll.appendChild(table);
      section.appendChild(scroll);
    }
    return section;
  }

  _buildCuotasHeader() {
    const head = DomBuilder.el("div", "exp-table__header");
    head.appendChild(DomBuilder.el("div", "exp-table__cell-date", "Fecha"));
    head.appendChild(DomBuilder.el("div", "exp-table__cell-desc", "Descripción"));
    head.appendChild(DomBuilder.el("div", "exp-table__cell-cat", "Categoría"));
    head.appendChild(DomBuilder.el("div", "exp-table__cell-installment", "Cuota"));
    head.appendChild(DomBuilder.el("div", "exp-table__cell-amount", "Valor cuota"));
    head.appendChild(DomBuilder.el("div", "exp-table__cell-amount", "Total compra"));
    head.appendChild(DomBuilder.el("div", "exp-table__cell-running", "Acumulado"));
    head.appendChild(DomBuilder.el("div", "exp-table__cell-actions"));
    return head;
  }

  _buildCuotaRow(row) {
    const node = DomBuilder.el("div", "exp-table__row");
    node.appendChild(DomBuilder.el("div", "exp-table__cell-date", row.occurred_on));
    node.appendChild(this._buildDescCell(row));
    node.appendChild(DomBuilder.el("div", "exp-table__cell-cat", row.category_caption));

    const cuotaCell = DomBuilder.el("div", "exp-table__cell-installment");
    cuotaCell.appendChild(DomBuilder.el("span", "exp-table__cuota-badge", `${row.installment_number}/${row.installments}`));
    node.appendChild(cuotaCell);

    node.appendChild(DomBuilder.el("div", "exp-table__cell-amount", CurrencyFormatter.formatCop(row.amount_cop)));

    const totalCell = DomBuilder.el("div", "exp-table__cell-amount");
    if (row.total_amount_cop > 0) {
      totalCell.appendChild(DomBuilder.el("span", null, CurrencyFormatter.formatCop(row.total_amount_cop)));
    } else {
      totalCell.appendChild(DomBuilder.el("span", "exp-table__muted", "—"));
    }
    node.appendChild(totalCell);

    node.appendChild(DomBuilder.el("div", "exp-table__cell-running", CurrencyFormatter.formatCop(row.running_total_cop)));
    node.appendChild(this._buildActions(row.expense_id));
    return node;
  }

  // ── Helpers compartidos ───────────────────────────────────────────────────

  _buildDescCell(row) {
    const cell = DomBuilder.el("div", "exp-table__cell-desc");
    cell.appendChild(DomBuilder.el("span", null, row.description || "—"));
    return cell;
  }

  _buildActions(expenseId) {
    const cell = DomBuilder.el("div", "exp-table__cell-actions");
    cell.appendChild(DomBuilder.button("exp-table__btn", "Editar", () => this._handlers.onEdit(expenseId)));
    cell.appendChild(DomBuilder.button("exp-table__btn exp-table__btn--danger", "Quitar", () => this._handlers.onDelete(expenseId)));
    return cell;
  }
}
