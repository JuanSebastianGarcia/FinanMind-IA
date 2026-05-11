import { DomBuilder } from "../core/dom_builder.js";
import { CardTile } from "./card_tile.js";
import { CardDialog } from "./dialogs/card_dialog.js";

export class CardsDashboardView {
  /** Renders the Tarjetas dashboard: topbar with Agregar + grid of tiles. */
  constructor(host, api, modal, toast, handlers) {
    this._host = host;
    this._api = api;
    this._modal = modal;
    this._toast = toast;
    this._handlers = handlers;
  }

  async render() {
    const state = await this._loadState();
    if (!state) return;
    const root = DomBuilder.el("div", "cards");
    root.appendChild(this._buildTopbar());
    root.appendChild(this._buildHint());
    root.appendChild(this._buildGrid(state.cards || []));
    this._host.appendChild(root);
  }

  async _loadState() {
    try {
      return await this._api.getCardsDashboardState();
    } catch (err) {
      this._toast.error(`No se pudieron cargar las tarjetas: ${CardsDashboardView._humanError(err)}`);
      return null;
    }
  }

  _buildTopbar() {
    const bar = DomBuilder.el("div", "cards__topbar");
    bar.appendChild(DomBuilder.el("div", "cards__topbar-title", "Tarjetas de crédito"));
    const actions = DomBuilder.el("div", "cards__topbar-actions");
    actions.appendChild(DomBuilder.button("btn btn--primary", "Agregar tarjeta", () => this._handleNewCard()));
    bar.appendChild(actions);
    return bar;
  }

  _buildHint() {
    return DomBuilder.el(
      "div",
      "cards__hint",
      "Administra tus tarjetas, sus gastos y pagos por ciclo de facturación.",
    );
  }

  _buildGrid(tiles) {
    const grid = DomBuilder.el("div", "tiles");
    if (tiles.length === 0) {
      grid.appendChild(this._buildEmpty());
      return grid;
    }
    for (const tile of tiles) {
      grid.appendChild(new CardTile(tile, this._handlers.onOpenCard).build());
    }
    return grid;
  }

  _buildEmpty() {
    const wrapper = DomBuilder.el("div", "tiles__empty");
    wrapper.appendChild(DomBuilder.el("div", "tiles__empty-title", "Sin tarjetas registradas"));
    wrapper.appendChild(
      DomBuilder.el("div", null, "Pulsa “Agregar tarjeta” para comenzar a registrar tus gastos."),
    );
    return wrapper;
  }

  async _handleNewCard() {
    const presets = await this._api.getCardsPalettePresets();
    const dialog = new CardDialog(this._modal, "Nueva tarjeta", presets, CardsDashboardView._cardSeed());
    const payload = await dialog.show();
    if (!payload) return;
    await this._saveNewCard(payload);
  }

  async _saveNewCard(payload) {
    try {
      const info = await this._api.addCard(
        payload.name, payload.limit, payload.cutDay, payload.dueDay, payload.color,
      );
      this._handlers.onCardCreated(info.card_id);
    } catch (err) {
      this._toast.error(`Tarjeta: ${CardsDashboardView._humanError(err)}`);
    }
  }

  static _cardSeed() {
    return { name: "", limit: 0, cutDay: 15, dueDay: 5, color: "" };
  }

  static _humanError(err) {
    if (err && err.message) return err.message;
    return String(err);
  }
}
