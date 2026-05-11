import { CardCategoriesPanel } from "./card_categories_panel.js";
import { CardChart } from "./card_chart.js";
import { CardCycleFilter } from "./card_cycle_filter.js";
import { CardDetailTopbar } from "./card_detail_topbar.js";
import { CardExpensesTable } from "./card_expenses_table.js";
import { CardPaymentsPanel } from "./card_payments_panel.js";
import { CardSummaryStrip } from "./card_summary_strip.js";
import { CardDialog } from "./dialogs/card_dialog.js";
import { CategoryDialog } from "./dialogs/category_dialog.js";
import { ConfirmDialog } from "../budget/dialogs/confirm_dialog.js";
import { DomBuilder } from "../core/dom_builder.js";
import { ExpenseDialog } from "./dialogs/expense_dialog.js";
import { PaymentDialog } from "./dialogs/payment_dialog.js";

export class CardDetailView {
  /** Orchestrates the single-card detail view: topbar, summary, filter, split layout. */
  constructor(host, api, modal, toast, context, handlers) {
    this._host = host;
    this._api = api;
    this._modal = modal;
    this._toast = toast;
    this._context = context;
    this._handlers = handlers;
    this._state = null;
  }

  async render() {
    const state = await this._loadState();
    if (!state) return;
    this._state = state;
    this._host.appendChild(this._buildLayout());
  }

  async _loadState() {
    try {
      return await this._api.getCardDetailState(this._context.cardId, this._context.cycleKey);
    } catch (err) {
      this._toast.error(`Tarjeta: ${CardDetailView._humanError(err)}`);
      this._handlers.onBack();
      return null;
    }
  }

  _buildLayout() {
    const root = DomBuilder.el("div", "detail");
    root.appendChild(new CardDetailTopbar(this._state.card, this._topbarHandlers()).build());
    root.appendChild(new CardSummaryStrip(this._state.summary).build());
    root.appendChild(new CardCycleFilter(this._state, this._handlers.onCycleChange).build());
    root.appendChild(this._buildSplit());
    return root;
  }

  _buildSplit() {
    const split = DomBuilder.el("div", "detail__split");
    split.appendChild(this._buildLeftColumn());
    split.appendChild(this._buildRightColumn());
    return split;
  }

  _buildLeftColumn() {
    const left = DomBuilder.el("div", "detail__column");
    left.appendChild(DomBuilder.el("div", "detail__section-title", "Movimientos del ciclo"));
    left.appendChild(new CardExpensesTable(this._state.expenses, this._expensesHandlers()).build());
    left.appendChild(DomBuilder.el("div", "detail__section-title", "Distribución por categoría"));
    left.appendChild(new CardChart(this._state.chart).build());
    return left;
  }

  _buildRightColumn() {
    const right = DomBuilder.el("div", "detail__column");
    right.appendChild(this._buildCategoriesHeader());
    right.appendChild(new CardCategoriesPanel(this._state.categories, this._categoryHandlers()).build());
    right.appendChild(DomBuilder.el("div", "detail__section-title", "Pagos registrados"));
    right.appendChild(new CardPaymentsPanel(this._state.payments, this._paymentHandlers()).build());
    return right;
  }

  _buildCategoriesHeader() {
    const head = DomBuilder.el("div", "cat-list__head");
    head.appendChild(DomBuilder.el("div", "detail__section-title", "Categorías"));
    head.appendChild(DomBuilder.button("btn btn--info", "Agregar", () => this._handleNewCategory()));
    return head;
  }

  _topbarHandlers() {
    return {
      onBack: () => this._handlers.onBack(),
      onEdit: () => this._handleEditCard(),
      onDelete: () => this._handleDeleteCard(),
      onNewPayment: () => this._handleNewPayment(),
      onNewExpense: () => this._handleNewExpense(),
    };
  }

  _expensesHandlers() {
    return {
      onEdit: (expenseId) => this._handleEditExpense(expenseId),
      onDelete: (expenseId) => this._handleDeleteExpense(expenseId),
    };
  }

  _categoryHandlers() {
    return {
      onEdit: (categoryId) => this._handleEditCategory(categoryId),
      onDelete: (categoryId) => this._handleDeleteCategory(categoryId),
    };
  }

  _paymentHandlers() {
    return { onDelete: (paymentId) => this._handleDeletePayment(paymentId) };
  }

  async _handleEditCard() {
    const presets = await this._api.getCardsPalettePresets();
    const seed = CardDetailView._seedFromCard(this._state.card);
    const payload = await new CardDialog(this._modal, "Editar tarjeta", presets, seed).show();
    if (!payload) return;
    await this._safelyMutate(
      () => this._api.updateCard(
        this._context.cardId, payload.name, payload.limit, payload.cutDay, payload.dueDay, payload.color,
      ),
      "Tarjeta",
    );
  }

  async _handleDeleteCard() {
    const ok = await this._askConfirm(
      "Eliminar tarjeta",
      "¿Eliminar esta tarjeta y todos sus gastos y pagos?",
    );
    if (!ok) return;
    try {
      await this._api.deleteCard(this._context.cardId);
      this._handlers.onCardDeleted();
    } catch (err) {
      this._toast.error(`Tarjeta: ${CardDetailView._humanError(err)}`);
    }
  }

  async _handleNewCategory() {
    const seed = { title: "", color: "", linkId: "" };
    const payload = await this._openCategoryDialog("Nueva categoría", seed);
    if (!payload) return;
    await this._safelyMutate(
      () => this._api.addCardCategory(this._context.cardId, payload.title, payload.color, payload.linkId),
      "Categoría",
    );
  }

  async _handleEditCategory(categoryId) {
    const cat = this._findCategory(categoryId);
    if (!cat) return;
    const seed = { title: cat.title, color: cat.color, linkId: cat.linked_label_id };
    const payload = await this._openCategoryDialog("Editar categoría", seed);
    if (!payload) return;
    await this._safelyMutate(
      () => this._api.updateCardCategory(categoryId, payload.title, payload.color, payload.linkId),
      "Categoría",
    );
  }

  async _openCategoryDialog(title, seed) {
    const presets = await this._api.getCardsPalettePresets();
    const options = await this._api.getCardsLabelOptions();
    return await new CategoryDialog(this._modal, title, presets, options, seed).show();
  }

  async _handleDeleteCategory(categoryId) {
    const ok = await this._askConfirm(
      "Eliminar categoría",
      "¿Eliminar esta categoría? Los gastos quedarán sin categoría.",
    );
    if (!ok) return;
    await this._safelyMutate(() => this._api.deleteCardCategory(categoryId), "Categoría");
  }

  async _handleNewExpense() {
    const seed = CardDetailView._emptyExpenseSeed();
    const payload = await this._openExpenseDialog("Nuevo gasto", seed);
    if (!payload) return;
    await this._safelyMutate(
      () => this._api.addCardExpense(
        this._context.cardId, payload.categoryId, payload.day, payload.amount,
        payload.description, payload.installments, payload.notes,
      ),
      "Gasto",
    );
  }

  async _handleEditExpense(expenseId) {
    const ex = this._findExpense(expenseId);
    if (!ex) return;
    const seed = CardDetailView._seedFromExpense(ex);
    const payload = await this._openExpenseDialog("Editar gasto", seed);
    if (!payload) return;
    await this._safelyMutate(
      () => this._api.updateCardExpense(
        expenseId, payload.categoryId, payload.day, payload.amount,
        payload.description, payload.installments, payload.notes,
      ),
      "Gasto",
    );
  }

  _openExpenseDialog(title, seed) {
    return new ExpenseDialog(this._modal, title, this._state.categories, seed).show();
  }

  async _handleDeleteExpense(expenseId) {
    const ok = await this._askConfirm("Eliminar gasto", "¿Eliminar este gasto?");
    if (!ok) return;
    await this._safelyMutate(() => this._api.deleteCardExpense(expenseId), "Gasto");
  }

  async _handleNewPayment() {
    const payload = await new PaymentDialog(this._modal).show();
    if (!payload) return;
    await this._safelyMutate(
      () => this._api.addCardPayment(this._context.cardId, payload.day, payload.amount, payload.notes),
      "Pago",
    );
  }

  async _handleDeletePayment(paymentId) {
    const ok = await this._askConfirm("Eliminar pago", "¿Eliminar este pago?");
    if (!ok) return;
    await this._safelyMutate(() => this._api.deleteCardPayment(paymentId), "Pago");
  }

  _findCategory(categoryId) {
    return (this._state.categories || []).find((c) => c.category_id === categoryId);
  }

  _findExpense(expenseId) {
    return (this._state.expenses || []).find((e) => e.expense_id === expenseId);
  }

  _askConfirm(title, message) {
    return new ConfirmDialog(this._modal, title, message).show();
  }

  async _safelyMutate(operation, contextLabel) {
    try {
      await operation();
      await this._reRender();
    } catch (err) {
      this._toast.error(`${contextLabel}: ${CardDetailView._humanError(err)}`);
    }
  }

  async _reRender() {
    this._host.innerHTML = "";
    await this.render();
  }

  static _seedFromCard(card) {
    return {
      name: card.name,
      limit: card.limit_cop,
      cutDay: card.cut_day,
      dueDay: card.payment_due_day,
      color: card.color,
    };
  }

  static _seedFromExpense(ex) {
    return {
      amount: ex.amount_cop,
      description: ex.description,
      categoryId: ex.category_id,
      day: ex.occurred_on,
      installments: ex.installments,
      notes: ex.notes,
    };
  }

  static _emptyExpenseSeed() {
    return { amount: 0, description: "", categoryId: "", day: "", installments: 1, notes: "" };
  }

  static _humanError(err) {
    if (err && err.message) return err.message;
    return String(err);
  }
}
