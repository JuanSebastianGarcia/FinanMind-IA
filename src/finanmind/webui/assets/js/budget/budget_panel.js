import { DomBuilder } from "../core/dom_builder.js";
import { BudgetTopbar } from "./budget_topbar.js";
import { SalaryCard } from "./salary_card.js";
import { CategoryGrid } from "./category_grid.js";
import { CategoryDialog } from "./dialogs/category_dialog.js";
import { LabelDialog } from "./dialogs/label_dialog.js";
import { SalaryDialog } from "./dialogs/salary_dialog.js";
import { ConfirmDialog } from "./dialogs/confirm_dialog.js";

export class BudgetPanel {
  /** Controls the entire Presupuesto interface: layout + dialog flows. */
  constructor(host, api, modal, toast) {
    this._host = host;
    this._api = api;
    this._modal = modal;
    this._toast = toast;
    this._topbar = null;
    this._salaryCard = null;
    this._grid = null;
    this._state = null;
  }

  async mount() {
    this._buildSkeleton();
    await this.refresh();
  }

  async refresh() {
    try {
      this._state = await this._api.getBudgetState();
    } catch (err) {
      this._toast.error(`No se pudo cargar el presupuesto: ${err}`);
      return;
    }
    this._renderState();
  }

  _buildSkeleton() {
    this._host.innerHTML = "";
    const outer = DomBuilder.el("div", "budget");
    this._topbar = new BudgetTopbar(outer, this._topbarHandlers());
    this._topbar.mount();
    this._salaryCard = new SalaryCard(outer);
    this._salaryCard.mount();
    outer.appendChild(DomBuilder.el("div", "budget__hint", "Datos en COP · porcentajes vs salario · budget.csv"));
    this._grid = new CategoryGrid(outer, this._gridHandlers());
    this._grid.mount();
    this._host.appendChild(outer);
  }

  _renderState() {
    if (!this._state) return;
    this._salaryCard.update(this._state.summary);
    this._grid.update(this._state.categories, this._state.salary_cop);
  }

  _topbarHandlers() {
    return {
      onAddCategory: () => this._handleAddCategory(),
      onEditSalary: () => this._handleEditSalary(),
      onOpenReview: () => this._handleOpenReview(),
    };
  }

  _gridHandlers() {
    return {
      onAddLabel: (catId) => this._handleAddLabel(catId),
      onEditCategory: (cat) => this._handleEditCategory(cat),
      onDeleteCategory: (catId) => this._handleDeleteCategory(catId),
      onEditLabel: (catId, label) => this._handleEditLabel(catId, label),
      onDeleteLabel: (catId, labelId) => this._handleDeleteLabel(catId, labelId),
    };
  }

  async _handleAddCategory() {
    const seed = await this._buildCategorySeed("", "");
    const payload = await new CategoryDialog(this._modal, seed.presets, seed.seed).show();
    if (!payload) return;
    await this._safelyMutate(
      () => this._api.addCategory(payload.title, payload.color),
      "Categoría",
    );
  }

  async _handleEditCategory(cat) {
    const seed = await this._buildCategorySeed(cat.title, cat.color);
    const payload = await new CategoryDialog(this._modal, seed.presets, seed.seed).show();
    if (!payload) return;
    await this._safelyMutate(
      () => this._api.updateCategory(cat.id, payload.title, payload.color),
      "Categoría",
    );
  }

  async _buildCategorySeed(title, color) {
    const presets = await this._api.getPalettePresets();
    const seedColor = color || (await this._api.nextPaletteColor());
    return { presets, seed: { title, color: seedColor } };
  }

  async _handleDeleteCategory(catId) {
    const ok = await this._askConfirm("Eliminar categoría", "¿Eliminar la categoría y todas sus etiquetas?");
    if (!ok) return;
    await this._safelyMutate(() => this._api.deleteCategory(catId), "Categoría");
  }

  async _handleEditSalary() {
    const current = this._state ? this._state.salary_cop : 0;
    const value = await new SalaryDialog(this._modal, current).show();
    if (value === null) return;
    await this._safelyMutate(() => this._api.setSalary(value), "Salario");
  }

  async _handleAddLabel(catId) {
    const seed = { title: "", amount: 0, linkId: "" };
    const payload = await this._showLabelDialog(seed);
    if (!payload) return;
    await this._safelyMutate(
      () => this._api.addLabel(catId, payload.title, payload.amount, payload.linkId),
      "Etiqueta",
    );
  }

  async _handleEditLabel(catId, label) {
    const seed = { title: label.title, amount: label.amount_cop, linkId: label.linked_cc_category_id };
    const payload = await this._showLabelDialog(seed);
    if (!payload) return;
    await this._safelyMutate(
      () => this._api.updateLabel(catId, label.id, payload.title, payload.amount, payload.linkId),
      "Etiqueta",
    );
  }

  async _showLabelDialog(seed) {
    const options = await this._api.getCcLinkOptions();
    return await new LabelDialog(this._modal, seed, options).show();
  }

  async _handleDeleteLabel(catId, labelId) {
    const ok = await this._askConfirm("Eliminar etiqueta", "¿Eliminar esta etiqueta?");
    if (!ok) return;
    await this._safelyMutate(() => this._api.deleteLabel(catId, labelId), "Etiqueta");
  }

  _askConfirm(title, message) {
    return new ConfirmDialog(this._modal, title, message).show();
  }

  _handleOpenReview() {
    this._toast.info("La revisión de presupuesto estará disponible próximamente.");
  }

  async _safelyMutate(operation, contextLabel) {
    try {
      this._state = await operation();
      this._renderState();
    } catch (err) {
      this._toast.error(`${contextLabel}: ${BudgetPanel._humanError(err)}`);
    }
  }

  static _humanError(err) {
    if (err && err.message) return err.message;
    return String(err);
  }
}
