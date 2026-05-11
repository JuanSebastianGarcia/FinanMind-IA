import { DomBuilder } from "../core/dom_builder.js";
import { CurrencyFormatter } from "../format/currency_formatter.js";
import { PercentFormatter } from "../format/percent_formatter.js";
import { LabelRow } from "./label_row.js";

export class CategoryCard {
  /** Renders one full column: header, stats, progress, label list. */
  constructor(category, salary, handlers) {
    this._cat = category;
    this._salary = salary;
    this._handlers = handlers;
    this._accent = CategoryCard._resolveAccent(category.color);
  }

  build() {
    const card = DomBuilder.el("div", "cat-card");
    card.appendChild(this._buildHeader());
    card.appendChild(this._buildStats());
    card.appendChild(this._buildProgress());
    card.appendChild(DomBuilder.el("div", "cat-card__separator"));
    card.appendChild(this._buildGridHeader());
    card.appendChild(this._buildLabelList());
    return card;
  }

  _buildHeader() {
    const header = DomBuilder.el("div", "cat-card__header");
    header.appendChild(this._buildTitleCell());
    header.appendChild(this._buildActionsCell());
    return header;
  }

  _buildTitleCell() {
    const cell = DomBuilder.el("div", "cat-card__title-cell");
    const dot = DomBuilder.el("span", "cat-card__dot");
    dot.style.background = this._accent;
    cell.appendChild(dot);
    cell.appendChild(DomBuilder.el("div", "cat-card__title", this._cat.title.toUpperCase()));
    return cell;
  }

  _buildActionsCell() {
    const cell = DomBuilder.el("div", "cat-card__actions");
    cell.appendChild(DomBuilder.button("chip-btn chip-btn--add", "+ Etiqueta", () => this._handlers.onAddLabel(this._cat.id)));
    cell.appendChild(DomBuilder.button("chip-btn chip-btn--edit", "Editar", () => this._handlers.onEditCategory(this._cat)));
    cell.appendChild(DomBuilder.button("chip-btn chip-btn--delete", "Eliminar", () => this._handlers.onDeleteCategory(this._cat.id)));
    return cell;
  }

  _buildStats() {
    const stats = DomBuilder.el("div", "cat-card__stats");
    const big = CategoryCard._formatBigPct(this._cat.percent_of_salary);
    stats.appendChild(DomBuilder.el("span", "cat-card__stats-big", big));
    const tail = `% del salario  ·  ${CurrencyFormatter.formatCop(this._cat.total_cop)}`;
    stats.appendChild(DomBuilder.el("span", "cat-card__stats-tail", tail));
    return stats;
  }

  _buildProgress() {
    const bar = DomBuilder.el("div", "cat-card__bar");
    const fill = DomBuilder.el("div", "cat-card__bar-fill");
    fill.style.width = `${Math.min(100, Math.max(0, this._cat.percent_of_salary))}%`;
    fill.style.background = this._accent;
    bar.appendChild(fill);
    return bar;
  }

  _buildGridHeader() {
    const row = DomBuilder.el("div", "cat-card__grid-header");
    row.appendChild(DomBuilder.el("div", "cat-card__grid-header-name", "Etiqueta"));
    row.appendChild(DomBuilder.el("div", "cat-card__grid-header-spacer", ""));
    row.appendChild(DomBuilder.el("div", "cat-card__grid-header-amount", "Importe / %"));
    row.appendChild(DomBuilder.el("div", "cat-card__grid-header-actions", ""));
    return row;
  }

  _buildLabelList() {
    const list = DomBuilder.el("div", "cat-card__labels");
    for (const label of this._cat.labels) {
      const row = new LabelRow(this._cat.id, label, this._salary, this._accent, this._handlers);
      list.appendChild(row.build());
    }
    return list;
  }

  static _resolveAccent(color) {
    const value = (color || "").trim();
    return value === "" ? "var(--accent)" : value;
  }

  static _formatBigPct(value) {
    return Number(value || 0).toFixed(1).replace(".", ",");
  }
}
