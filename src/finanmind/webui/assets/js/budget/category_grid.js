import { DomBuilder } from "../core/dom_builder.js";
import { CategoryCard } from "./category_card.js";

export class CategoryGrid {
  /** Horizontal scroll region that hosts one CategoryCard per category. */
  constructor(host, handlers) {
    this._host = host;
    this._handlers = handlers;
    this._grid = null;
    this._salary = 0;
  }

  mount() {
    this._grid = DomBuilder.el("div", "category-grid");
    this._host.appendChild(this._grid);
  }

  update(categories, salary) {
    this._salary = Number(salary) || 0;
    this._grid.innerHTML = "";
    if (!categories || categories.length === 0) {
      this._grid.appendChild(this._buildEmptyState());
      return;
    }
    for (const cat of categories) {
      const card = new CategoryCard(cat, this._salary, this._handlers);
      this._grid.appendChild(card.build());
    }
  }

  _buildEmptyState() {
    const message = 'Sin categorías todavía. Pulsa "Agregar categoría".';
    return DomBuilder.el("div", "category-empty", message);
  }
}
