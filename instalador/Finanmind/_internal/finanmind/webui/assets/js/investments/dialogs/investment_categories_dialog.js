import { ConfirmDialog } from "../../budget/dialogs/confirm_dialog.js";
import { DomBuilder } from "../../core/dom_builder.js";
import { InvestmentCategoryEditorDialog } from "./investment_category_editor_dialog.js";

export class InvestmentCategoriesDialog {
  /** Lists categories with add, rename, delete; supports chaining sub-dialogs. */
  constructor(modalHost, toast, api) {
    this._host = modalHost;
    this._toast = toast;
    this._api = api;
    this._resolver = null;
    this._listEl = null;
    this._categories = [];
    this._changed = false;
    this._navigating = false;
  }

  show(categories) {
    this._categories = Array.isArray(categories) ? categories.slice() : [];
    return new Promise((resolve) => {
      this._resolver = resolve;
      this._mount();
    });
  }

  _mount() {
    this._host.open(this._build(), () => this._handleHostClose());
    this._renderRows();
  }

  _handleHostClose() {
    if (this._navigating) return;
    const resolver = this._resolver;
    this._resolver = null;
    if (resolver) resolver({ changed: this._changed });
  }

  _build() {
    const modal = DomBuilder.el("div", "modal modal--wide");
    modal.appendChild(DomBuilder.el("div", "modal__title", "Categorías de inversión"));
    modal.appendChild(this._buildHint());
    modal.appendChild(DomBuilder.button("btn btn--primary", "Nueva categoría", () => this._handleAdd()));
    this._listEl = DomBuilder.el("div", "rules-list");
    modal.appendChild(this._listEl);
    modal.appendChild(this._buildActions());
    return modal;
  }

  _buildHint() {
    return DomBuilder.el(
      "div",
      "modal__field-label",
      "Tus categorías (nombre = activo en el que inviertes).",
    );
  }

  _buildActions() {
    const actions = DomBuilder.el("div", "modal__actions");
    actions.appendChild(DomBuilder.button("btn btn--outline", "Cerrar", () => this._host.close()));
    return actions;
  }

  _renderRows() {
    if (!this._listEl) return;
    this._listEl.innerHTML = "";
    if (this._categories.length === 0) {
      this._listEl.appendChild(this._buildEmpty());
      return;
    }
    for (const cat of this._categories) this._listEl.appendChild(this._buildRow(cat));
  }

  _buildEmpty() {
    return DomBuilder.el(
      "div",
      "rules-list__empty",
      "Aún no hay categorías. Crea la primera para registrar inversiones.",
    );
  }

  _buildRow(cat) {
    const row = DomBuilder.el("div", "rules-list__row");
    row.appendChild(DomBuilder.el("div", "rules-list__text", cat.name || ""));
    row.appendChild(this._buildRowActions(cat));
    return row;
  }

  _buildRowActions(cat) {
    const wrap = DomBuilder.el("div", "rules-list__actions");
    wrap.appendChild(DomBuilder.button("invest-card__btn", "Editar", () => this._handleEdit(cat)));
    wrap.appendChild(DomBuilder.button(
      "invest-card__btn invest-card__btn--danger",
      "Eliminar",
      () => this._handleDelete(cat),
    ));
    return wrap;
  }

  async _handleAdd() {
    const value = await this._chainDialog(
      new InvestmentCategoryEditorDialog(this._host, "Nueva categoría", ""),
    );
    if (!value) return;
    await this._mutate(() => this._api.addInvestmentCategory(value));
  }

  async _handleEdit(cat) {
    const value = await this._chainDialog(
      new InvestmentCategoryEditorDialog(this._host, "Editar categoría", cat.name || ""),
    );
    if (!value) return;
    await this._mutate(() => this._api.updateInvestmentCategory(cat.category_id, value));
  }

  async _handleDelete(cat) {
    const ok = await this._chainDialog(new ConfirmDialog(
      this._host,
      "Eliminar categoría",
      `¿Eliminar la categoría «${cat.name || "(sin nombre)"}»?`,
    ));
    if (!ok) return;
    await this._mutate(() => this._api.deleteInvestmentCategory(cat.category_id));
  }

  async _chainDialog(dialog) {
    this._navigating = true;
    const value = await dialog.show();
    this._navigating = false;
    this._mount();
    return value;
  }

  async _mutate(operation) {
    try {
      const state = await operation();
      this._categories = (state && state.categories) || [];
      this._changed = true;
      this._renderRows();
    } catch (err) {
      this._toast.error(`Categoría: ${InvestmentCategoriesDialog._humanError(err)}`);
    }
  }

  static _humanError(err) {
    if (err && err.message) return err.message;
    return String(err);
  }
}
