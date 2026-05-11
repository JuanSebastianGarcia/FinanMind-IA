import { DomBuilder } from "../core/dom_builder.js";

export class BudgetTopbar {
  /** Title row with Agregar categoría, Editar salario, and Revisión buttons. */
  constructor(host, handlers) {
    this._host = host;
    this._handlers = handlers;
  }

  mount() {
    const bar = DomBuilder.el("div", "budget__topbar");
    bar.appendChild(DomBuilder.el("div", "budget__topbar-title", "Gestión del presupuesto"));
    bar.appendChild(this._buildActions());
    this._host.appendChild(bar);
  }

  _buildActions() {
    const actions = DomBuilder.el("div", "budget__topbar-actions");
    actions.appendChild(this._reviewButton());
    actions.appendChild(this._editSalaryButton());
    actions.appendChild(this._addCategoryButton());
    return actions;
  }

  _addCategoryButton() {
    return DomBuilder.button("btn btn--primary", "Agregar categoría", () => this._handlers.onAddCategory());
  }

  _editSalaryButton() {
    return DomBuilder.button("btn btn--outline", "Editar salario", () => this._handlers.onEditSalary());
  }

  _reviewButton() {
    return DomBuilder.button("btn btn--info", "Revisión de presupuesto", () => this._handlers.onOpenReview());
  }
}
