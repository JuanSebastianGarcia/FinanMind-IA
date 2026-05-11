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

  getCardsDashboardState() {
    return this._api.get_cards_dashboard_state();
  }

  getCardDetailState(cardId, preferredCycle) {
    return this._api.get_card_detail_state(cardId, preferredCycle || "");
  }

  getCardsLabelOptions() {
    return this._api.get_cards_label_options();
  }

  getCardsPalettePresets() {
    return this._api.get_cards_palette_presets();
  }

  addCard(name, limit, cutDay, paymentDueDay, color) {
    return this._api.add_card(name, limit, cutDay, paymentDueDay, color || "");
  }

  updateCard(cardId, name, limit, cutDay, paymentDueDay, color) {
    return this._api.update_card(cardId, name, limit, cutDay, paymentDueDay, color || "");
  }

  deleteCard(cardId) {
    return this._api.delete_card(cardId);
  }

  addCardCategory(cardId, title, color, linkId) {
    return this._api.add_card_category(cardId, title, color || "", linkId || "");
  }

  updateCardCategory(categoryId, title, color, linkId) {
    return this._api.update_card_category(categoryId, title, color || "", linkId || "");
  }

  deleteCardCategory(categoryId) {
    return this._api.delete_card_category(categoryId);
  }

  addCardExpense(cardId, categoryId, occurredOn, amount, description, installments, notes) {
    return this._api.add_card_expense(
      cardId, categoryId || "", occurredOn, amount, description, installments || 1, notes || "",
    );
  }

  updateCardExpense(expenseId, categoryId, occurredOn, amount, description, installments, notes) {
    return this._api.update_card_expense(
      expenseId, categoryId || "", occurredOn, amount, description, installments || 1, notes || "",
    );
  }

  deleteCardExpense(expenseId) {
    return this._api.delete_card_expense(expenseId);
  }

  addCardPayment(cardId, paidOn, amount, notes) {
    return this._api.add_card_payment(cardId, paidOn, amount, notes || "");
  }

  deleteCardPayment(paymentId) {
    return this._api.delete_card_payment(paymentId);
  }

  getInvestmentsState() {
    return this._api.get_investments_state();
  }

  addInvestmentCategory(name) {
    return this._api.add_investment_category(name);
  }

  updateInvestmentCategory(categoryId, name) {
    return this._api.update_investment_category(categoryId, name);
  }

  deleteInvestmentCategory(categoryId) {
    return this._api.delete_investment_category(categoryId);
  }

  addInvestmentEntry(categoryId, amount, investedDateIso, description, currencyCode) {
    return this._api.add_investment_entry(
      categoryId, amount, investedDateIso, description || "", currencyCode,
    );
  }

  updateInvestmentEntry(investmentId, categoryId, amount, investedDateIso, description, currencyCode) {
    return this._api.update_investment_entry(
      investmentId, categoryId, amount, investedDateIso, description || "", currencyCode,
    );
  }

  deleteInvestmentEntry(investmentId) {
    return this._api.delete_investment_entry(investmentId);
  }

  getInvestmentReviewSetup() {
    return this._api.get_investment_review_setup();
  }

  addInvestmentReviewRule(text) {
    return this._api.add_investment_review_rule(text);
  }

  updateInvestmentReviewRule(ruleId, text) {
    return this._api.update_investment_review_rule(ruleId, text);
  }

  deleteInvestmentReviewRule(ruleId) {
    return this._api.delete_investment_review_rule(ruleId);
  }

  runInvestmentReview(rate) {
    return this._api.run_investment_review(rate);
  }

  getDashboardState(preferredMonth) {
    return this._api.get_dashboard_state(preferredMonth || "");
  }

  getBudgetReviewSetup() {
    return this._api.get_budget_review_setup();
  }

  setBudgetReviewProvider(vendor) {
    return this._api.set_budget_review_provider(vendor || "");
  }

  runBudgetReview(context) {
    return this._api.run_budget_review(context || "");
  }

  applyBudgetReviewRecommendations(recommendations) {
    return this._api.apply_budget_review_recommendations(recommendations || []);
  }

  getBudgetReviewLlmSettings() {
    return this._api.get_budget_review_llm_settings();
  }

  saveBudgetReviewLlmSettings(provider, apiKey, modelId) {
    return this._api.save_budget_review_llm_settings(provider || "", apiKey || "", modelId || "");
  }
}
