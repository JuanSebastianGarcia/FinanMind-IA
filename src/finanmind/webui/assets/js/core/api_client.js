export class ApiClient {
  /** Wraps ``window.pywebview.api`` with named, camel-cased methods. */
  constructor() {
    this._api = window.pywebview.api;
  }

  getBudgetState() {
    return this._api.get_budget_state();
  }

  setSalary(amount) {
    return this._api.set_salary(amount);
  }

  addCategory(title, color) {
    return this._api.add_category(title, color);
  }

  updateCategory(categoryId, title, color) {
    return this._api.update_category(categoryId, title, color);
  }

  deleteCategory(categoryId) {
    return this._api.delete_category(categoryId);
  }

  addLabel(categoryId, title, amount, linkId) {
    return this._api.add_label(categoryId, title, amount, linkId);
  }

  updateLabel(categoryId, labelId, title, amount, linkId) {
    return this._api.update_label(categoryId, labelId, title, amount, linkId);
  }

  deleteLabel(categoryId, labelId) {
    return this._api.delete_label(categoryId, labelId);
  }

  nextPaletteColor() {
    return this._api.next_palette_color();
  }

  getPalettePresets() {
    return this._api.get_palette_presets();
  }

  getCcLinkOptions() {
    return this._api.get_cc_link_options();
  }

  getDistributionState(preferredMonth, preferredReceiptId) {
    return this._api.get_distribution_state(preferredMonth || "", preferredReceiptId || "");
  }

  getDistributionLabelOptions() {
    return this._api.get_distribution_label_options();
  }

  addDistributionReceipt(occurredOn, amount, memo) {
    return this._api.add_distribution_receipt(occurredOn, amount, memo || "");
  }

  deleteDistributionReceipt(receiptId) {
    return this._api.delete_distribution_receipt(receiptId);
  }

  addDistributionLine(receiptId, labelId, occurredOn, amount, memo) {
    return this._api.add_distribution_line(receiptId, labelId, occurredOn, amount, memo || "");
  }

  deleteDistributionLine(lineId) {
    return this._api.delete_distribution_line(lineId);
  }
}
