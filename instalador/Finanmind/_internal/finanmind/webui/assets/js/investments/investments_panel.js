import { ConfirmDialog } from "../budget/dialogs/confirm_dialog.js";
import { DomBuilder } from "../core/dom_builder.js";
import { InvestmentCategoriesDialog } from "./dialogs/investment_categories_dialog.js";
import { InvestmentEntryDialog } from "./dialogs/investment_entry_dialog.js";
import { InvestmentReviewDialog } from "./dialogs/investment_review_dialog.js";
import { InvestmentsCurrencyChartBlock } from "./investments_currency_chart_block.js";
import { InvestmentsList } from "./investments_list.js";
import { InvestmentsSummaryStrip } from "./investments_summary_strip.js";
import { InvestmentsTopbar } from "./investments_topbar.js";

export class InvestmentsPanel {
  /** Top-level Inversiones panel: topbar, summary, list and donut charts. */
  constructor(host, api, modal, toast) {
    this._host = host;
    this._api = api;
    this._modal = modal;
    this._toast = toast;
    this._state = null;
  }

  async mount() {
    this._host.innerHTML = "";
    await this.refresh();
  }

  async refresh() {
    const state = await this._loadState();
    if (!state) return;
    this._state = state;
    this._render();
  }

  async _loadState() {
    try {
      return await this._api.getInvestmentsState();
    } catch (err) {
      this._toast.error(`Inversiones: ${InvestmentsPanel._humanError(err)}`);
      return null;
    }
  }

  _render() {
    this._host.innerHTML = "";
    const root = DomBuilder.el("div", "invest");
    root.appendChild(new InvestmentsTopbar(this._topbarHandlers()).build());
    root.appendChild(this._buildHint());
    root.appendChild(new InvestmentsSummaryStrip(this._state.summary).build());
    root.appendChild(this._buildBody());
    this._host.appendChild(root);
  }

  _buildHint() {
    return DomBuilder.el(
      "div",
      "invest__hint",
      "Define categorías (nombre = activo); cada inversión usa una categoría y moneda COP o USD.",
    );
  }

  _buildBody() {
    const body = DomBuilder.el("div", "invest__body");
    body.appendChild(this._buildLeftColumn());
    body.appendChild(this._buildRightColumn());
    return body;
  }

  _buildLeftColumn() {
    const col = DomBuilder.el("div", "invest__col");
    col.appendChild(new InvestmentsList(this._state.entries, this._listHandlers()).build());
    return col;
  }

  _buildRightColumn() {
    const col = DomBuilder.el("div", "invest__col");
    const scroll = DomBuilder.el("div", "invest__col-scroll");
    scroll.appendChild(new InvestmentsCurrencyChartBlock(
      "Distribución en COP por categoría",
      "COP",
      this._state.distribution_cop,
    ).build());
    scroll.appendChild(new InvestmentsCurrencyChartBlock(
      "Distribución en USD por categoría",
      "USD",
      this._state.distribution_usd,
    ).build());
    col.appendChild(scroll);
    return col;
  }

  _topbarHandlers() {
    return {
      onNewEntry: () => this._handleNewEntry(),
      onOpenIa: () => this._handleOpenIa(),
      onOpenCategories: () => this._handleOpenCategories(),
    };
  }

  _listHandlers() {
    return {
      onEdit: (id) => this._handleEditEntry(id),
      onDelete: (id) => this._handleDeleteEntry(id),
    };
  }

  async _handleNewEntry() {
    if (!this._hasCategories()) {
      this._toast.info("Crea primero al menos una categoría.");
      return;
    }
    const seed = InvestmentsPanel._emptyEntrySeed();
    const payload = await new InvestmentEntryDialog(this._modal, "Nueva inversión", this._state.categories, seed).show();
    if (!payload) return;
    await this._safelyMutate(() => this._api.addInvestmentEntry(
      payload.categoryId, payload.amount, payload.investedDateIso, payload.description, payload.currencyCode,
    ));
  }

  async _handleEditEntry(investmentId) {
    const entry = this._findEntry(investmentId);
    if (!entry) return;
    const seed = InvestmentsPanel._seedFromEntry(entry);
    const payload = await new InvestmentEntryDialog(this._modal, "Editar inversión", this._state.categories, seed).show();
    if (!payload) return;
    await this._safelyMutate(() => this._api.updateInvestmentEntry(
      investmentId, payload.categoryId, payload.amount, payload.investedDateIso, payload.description, payload.currencyCode,
    ));
  }

  async _handleDeleteEntry(investmentId) {
    const ok = await new ConfirmDialog(this._modal, "Eliminar inversión", "¿Eliminar esta inversión?").show();
    if (!ok) return;
    await this._safelyMutate(() => this._api.deleteInvestmentEntry(investmentId));
  }

  async _handleOpenCategories() {
    const dlg = new InvestmentCategoriesDialog(this._modal, this._toast, this._api);
    const result = await dlg.show(this._state.categories || []);
    if (result && result.changed) await this.refresh();
  }

  async _handleOpenIa() {
    if (!this._hasEntries()) {
      this._toast.info("Registra al menos una inversión antes de pedir un análisis.");
      return;
    }
    const dlg = new InvestmentReviewDialog(this._modal, this._toast, this._api);
    await dlg.show();
  }

  _hasCategories() {
    return Array.isArray(this._state.categories) && this._state.categories.length > 0;
  }

  _hasEntries() {
    return Array.isArray(this._state.entries) && this._state.entries.length > 0;
  }

  _findEntry(investmentId) {
    return (this._state.entries || []).find((e) => e.investment_id === investmentId);
  }

  async _safelyMutate(operation) {
    try {
      const state = await operation();
      if (state) this._state = state;
      this._render();
    } catch (err) {
      this._toast.error(`Inversiones: ${InvestmentsPanel._humanError(err)}`);
    }
  }

  static _emptyEntrySeed() {
    return {
      category_id: "",
      amount: 0,
      currency_code: "COP",
      invested_date_iso: "",
      description: "",
    };
  }

  static _seedFromEntry(entry) {
    return {
      category_id: entry.category_id,
      amount: entry.amount,
      currency_code: entry.currency_code,
      invested_date_iso: entry.invested_date_iso,
      description: entry.description,
    };
  }

  static _humanError(err) {
    if (err && err.message) return err.message;
    return String(err);
  }
}
