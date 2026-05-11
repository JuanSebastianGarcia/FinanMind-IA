import { DomBuilder } from "../core/dom_builder.js";

export class InvestmentsTopbar {
  /** Title + "Nueva inversión" (primary), "Análisis IA" (info), "Categorías" (outline). */
  constructor(handlers) {
    this._handlers = handlers || {};
  }

  build() {
    const bar = DomBuilder.el("div", "invest__topbar");
    bar.appendChild(DomBuilder.el("div", "invest__topbar-title", "Gestión de inversiones"));
    bar.appendChild(this._buildActions());
    return bar;
  }

  _buildActions() {
    const actions = DomBuilder.el("div", "invest__topbar-actions");
    actions.appendChild(this._buildCategoriesBtn());
    actions.appendChild(this._buildAiBtn());
    actions.appendChild(this._buildNewBtn());
    return actions;
  }

  _buildCategoriesBtn() {
    return DomBuilder.button("btn btn--outline", "Categorías", () => this._fire("onOpenCategories"));
  }

  _buildAiBtn() {
    return DomBuilder.button("btn btn--info", "Análisis IA", () => this._fire("onOpenIa"));
  }

  _buildNewBtn() {
    return DomBuilder.button("btn btn--primary", "Nueva inversión", () => this._fire("onNewEntry"));
  }

  _fire(name) {
    const handler = this._handlers[name];
    if (typeof handler === "function") handler();
  }
}
