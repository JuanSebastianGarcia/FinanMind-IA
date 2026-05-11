import { DomBuilder } from "../core/dom_builder.js";

export class CardCategoriesPanel {
  /** Right-side categories list with swatch, link caption, and row actions. */
  constructor(rows, handlers) {
    this._rows = rows || [];
    this._handlers = handlers;
  }

  build() {
    const scroll = DomBuilder.el("div", "detail__card-scroll");
    if (this._rows.length === 0) {
      const msg = "Sin categorías. Crea la primera para clasificar tus gastos.";
      scroll.appendChild(DomBuilder.el("div", "detail__empty", msg));
      return scroll;
    }
    const container = DomBuilder.el("div", "cat-list");
    for (const row of this._rows) container.appendChild(this._buildRow(row));
    scroll.appendChild(container);
    return scroll;
  }

  _buildRow(row) {
    const node = DomBuilder.el("div", "cat-list__row");
    node.appendChild(this._buildSwatch(row.color));
    node.appendChild(this._buildBody(row));
    node.appendChild(this._buildActions(row.category_id));
    return node;
  }

  _buildSwatch(color) {
    const swatch = DomBuilder.el("div", "cat-list__swatch");
    swatch.style.background = color || "var(--border)";
    return swatch;
  }

  _buildBody(row) {
    const body = DomBuilder.el("div", "cat-list__body");
    body.appendChild(DomBuilder.el("div", "cat-list__title", row.title));
    if (row.link_caption) {
      body.appendChild(DomBuilder.el("div", "cat-list__link", row.link_caption));
    }
    return body;
  }

  _buildActions(categoryId) {
    const cell = DomBuilder.el("div", "cat-list__actions");
    cell.appendChild(DomBuilder.button("cat-list__btn", "Editar", () => this._handlers.onEdit(categoryId)));
    cell.appendChild(DomBuilder.button("cat-list__btn cat-list__btn--delete", "✕", () => this._handlers.onDelete(categoryId)));
    return cell;
  }
}
