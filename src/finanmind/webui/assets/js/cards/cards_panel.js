import { CardsDashboardView } from "./cards_dashboard_view.js";
import { CardDetailView } from "./card_detail_view.js";

export class CardsPanel {
  /** Top-level Deudas panel that swaps between the dashboard and a card detail. */
  constructor(host, api, modal, toast) {
    this._host = host;
    this._api = api;
    this._modal = modal;
    this._toast = toast;
    this._view = "dashboard";
    this._cardId = "";
    this._cycleKey = "";
    this._inner = null;
  }

  async mount() {
    this._host.innerHTML = "";
    this._inner = document.createElement("div");
    this._inner.className = "cards-root";
    this._host.appendChild(this._inner);
    await this.refresh();
  }

  async refresh() {
    if (this._view === "detail") {
      await this._renderDetail();
      return;
    }
    await this._renderDashboard();
  }

  async _renderDashboard() {
    this._inner.innerHTML = "";
    const view = this._buildDashboardView();
    await view.render();
  }

  _buildDashboardView() {
    return new CardsDashboardView(
      this._inner,
      this._api,
      this._modal,
      this._toast,
      this._dashboardHandlers(),
    );
  }

  _dashboardHandlers() {
    return {
      onOpenCard: (cardId) => this._gotoDetail(cardId),
      onCardCreated: (cardId) => this._gotoDetail(cardId),
    };
  }

  async _renderDetail() {
    this._inner.innerHTML = "";
    const view = this._buildDetailView();
    await view.render();
  }

  _buildDetailView() {
    return new CardDetailView(
      this._inner,
      this._api,
      this._modal,
      this._toast,
      this._detailContext(),
      this._detailHandlers(),
    );
  }

  _detailContext() {
    return { cardId: this._cardId, cycleKey: this._cycleKey };
  }

  _detailHandlers() {
    return {
      onBack: () => this._gotoDashboard(),
      onCardDeleted: () => this._gotoDashboard(),
      onCycleChange: (key) => this._setCycle(key),
    };
  }

  async _gotoDetail(cardId) {
    this._view = "detail";
    this._cardId = cardId;
    this._cycleKey = "";
    await this.refresh();
  }

  async _gotoDashboard() {
    this._view = "dashboard";
    this._cardId = "";
    this._cycleKey = "";
    await this.refresh();
  }

  async _setCycle(key) {
    this._cycleKey = key || "";
    await this.refresh();
  }
}
